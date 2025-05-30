# this python script runs jepa
from pathlib import Path
import time
import datetime
import os
import shutil
import random
import logging
from typing import Union
import yaml
import pprint
import torch
import torch.nn.functional as F
#import torch.nn.SmoothL1Loss as S1L

from PIL import Image

from waggle.plugin import Plugin


import numpy as np

from source.datasets.ptz_dataset import get_position_datetime_from_labels
from source.prepare_dataset import (
    collect_commands,
    collect_embeds_rewards,
    collect_images,
    collect_positions,
    grab_image, grab_position,
    set_random_position,
    set_relative_position,
    get_dirs,
    verify_image
)


from source.helper import (
    load_checkpoint,
    init_world_model,
    init_agent_model
)
from source.track_progress import timefmt, update_progress


from source.transforms import make_transforms

#from source.datasets.ptz_dataset import PTZImageDataset

# --
#log_timings = True
log_freq = 10
checkpoint_freq = 50000000000000
# --
logger = logging.getLogger(__name__)


def control_ptz(args, params, resume_preempt=False):
    # ----------------------------------------------------------------------- #
    #  PASSED IN PARAMS FROM CONFIG FILE
    # ----------------------------------------------------------------------- #

    # -- META
    use_bfloat16 = params['meta']['use_bfloat16']
    model_arch = params['meta']['agent_model_arch']
    wm_model_arch = model_arch
    agent_model_arch = model_arch
    load_model = params['meta']['load_checkpoint'] or resume_preempt
    r_file = params['meta']['read_checkpoint']
    pred_depth = params['meta']['pred_depth']
    pred_emb_dim = params['meta']['pred_emb_dim']
    camerabrand = params['meta']['camera_brand']
    if not torch.cuda.is_available():
        device = torch.device('cpu')
    else:
        device = torch.device('cuda:0')
        torch.cuda.set_device(device)

    # -- DATA
    use_gaussian_blur = params['data']['use_gaussian_blur']
    use_horizontal_flip = params['data']['use_horizontal_flip']
    use_color_distortion = params['data']['use_color_distortion']
    color_jitter = params['data']['color_jitter_strength']
    # --
    crop_size = params['data']['crop_size']
    crop_scale = params['data']['crop_scale']

    # -- MASK
    patch_size = params['mask']['patch_size']  # patch-size for model training
    # --

    # -- LOGGING
    folder = params['logging']['folder']
    agent_folder = params['logging']['agent_folder']
    dream_folder = params['logging']['dream_folder']
    ownership_folder = params['logging']['ownership_folder']
    tag = params['logging']['write_tag']

    # -- ACTIONS
    action_noop = params['action']['noop']
    action_short_left = params['action']['short']['left']
    action_short_right = params['action']['short']['right']
    action_short_left_up = params['action']['short']['left_up']
    action_short_right_up = params['action']['short']['right_up']
    action_short_left_down = params['action']['short']['left_down']
    action_short_right_down = params['action']['short']['right_down']
    action_short_up = params['action']['short']['up']
    action_short_down = params['action']['short']['down']
    action_short_zoom_in = params['action']['short']['zoom_in']
    action_short_zoom_out = params['action']['short']['zoom_out']

    action_long_left = params['action']['long']['left']
    action_long_right = params['action']['long']['right']
    action_long_up = params['action']['long']['up']
    action_long_down = params['action']['long']['down']
    action_long_zoom_in = params['action']['long']['zoom_in']
    action_long_zoom_out = params['action']['long']['zoom_out']

    action_jump_left = params['action']['jump']['left']
    action_jump_right = params['action']['jump']['right']
    action_jump_up = params['action']['jump']['up']
    action_jump_down = params['action']['jump']['down']

    actions={}
    actions[0]=action_noop
    actions[1]=action_short_left
    actions[2]=action_short_right
    actions[3]=action_short_left_up
    actions[4]=action_short_right_up
    actions[5]=action_short_left_down
    actions[6]=action_short_right_down
    actions[7]=action_short_up
    actions[8]=action_short_down
    actions[9]=action_short_zoom_in
    actions[10]=action_short_zoom_out
    actions[11]=action_long_left
    actions[12]=action_long_right
    actions[13]=action_long_up
    actions[14]=action_long_down
    actions[15]=action_long_zoom_in
    actions[16]=action_long_zoom_out
    actions[17]=action_jump_left
    actions[18]=action_jump_right
    actions[19]=action_jump_up
    actions[20]=action_jump_down

    num_actions=len(actions.keys())

    if not os.path.exists(folder) or not os.path.exists(agent_folder):
        print('No world models or agents to use the camera')
        return False


    world_models=[]
    for subdir in os.listdir(folder):
        world_models.append(subdir)

    if len(world_models)==0:
        print('No world models to use the camera')
        return False

    agents=[]
    for subdir in os.listdir(agent_folder):
        agents.append(subdir)

    if len(agents)==0:
        print('No agents to use the camera')
        return False

    # Need to determine the id to use here
    # world_model_name=random.sample(world_models,1)[0]
    # agent_name=random.sample(agents,1)[0]
    # choose a random agent and use its corresponding parent WM encoder
    persis_dir, coll_dir, tmp_dir = get_dirs()
    wm_dir = persis_dir / "world_models"
    ag_dir = persis_dir / "agents"
    agent_name = random.choice(agents)
    with open(ag_dir / agent_name / "model_info.yaml", "r") as f:
        info_dict = yaml.safe_load(f)

    if info_dict['num_restart'] < 0:
        # Initialize restart counter if it's negative
        info_dict['num_restart'] = 0
        info_dict[f"restart_{info_dict['num_restart']:0>2}"] = {
            "start_ind": 0,
            "rew_sum": 0,
            "target_rew": 0,
            "num_steps": 0
        }
    
    restart_info = info_dict[f"restart_{info_dict['num_restart']:0>2}"]
    
    world_model_name = restart_info["parent_model"]
    # ----------------------------------------------------------------------- #
    #   Bring world model first
    # ----------------------------------------------------------------------- #

    print('world_model_name: ', world_model_name)

    # -- log/checkpointing paths
    log_file = os.path.join(folder, world_model_name, f'{tag}.csv')
    save_path = os.path.join(folder, world_model_name, f'{tag}' + '-ep{epoch}.pt')
    latest_path = os.path.join(folder, world_model_name, f'{tag}-latest.pt')
    load_path = None
    if load_model:
        load_path = os.path.join(folder, r_file) if r_file is not None else latest_path

    print('log_file ', log_file)
    print('save_path ', save_path)
    print('latest_path ', latest_path)
    print('load_path ', load_path)

    # -- init world model
    target_encoder, _ = init_world_model(
        device=device,
        patch_size=patch_size,
        crop_size=crop_size,
        pred_depth=pred_depth,
        pred_emb_dim=pred_emb_dim,
        model_arch=wm_model_arch) # agent and world model are using the same encoder

    # -- make data transforms
    transform = make_transforms(
        crop_size=crop_size,
        crop_scale=crop_scale,
        gaussian_blur=use_gaussian_blur,
        horizontal_flip=use_horizontal_flip,
        color_distortion=use_color_distortion,
        color_jitter=color_jitter)

    for p in target_encoder.parameters():
        p.requires_grad = False

    # -- load training checkpoint
    if load_model:
        _, _, target_encoder, _, _, _ = load_checkpoint(
            device=device,
            r_path=load_path,
            target_encoder=target_encoder)



    # ----------------------------------------------------------------------- #
    #   Bring agent model
    # ----------------------------------------------------------------------- #

    print('agent_name: ', agent_name)

    # -- log/checkpointing paths
    agent_log_file = os.path.join(agent_folder, agent_name, f'{tag}.csv')
    agent_save_path = os.path.join(agent_folder, agent_name, f'{tag}' + '-ep{epoch}.pt')
    agent_target_latest_path = os.path.join(agent_folder, agent_name, f'{tag}-target_latest.pt')
    agent_target_load_path = None
    if load_model:
        agent_target_load_path = os.path.join(agent_folder, r_file) if r_file is not None else agent_target_latest_path

    print('agent_log_file ', agent_log_file)
    print('agent_save_path ', agent_save_path)
    print('agent_target_latest_path ', agent_target_latest_path)
    print('agent_target_load_path ', agent_target_load_path)

    # -- init agent model
    _, target_predictor = init_agent_model(
        device=device,
        patch_size=patch_size,
        crop_size=crop_size,
        pred_depth=pred_depth,
        pred_emb_dim=pred_emb_dim,
        model_arch=agent_model_arch,
        num_actions=num_actions)

    for p in target_predictor.parameters():
        p.requires_grad = False

    # -- load training checkpoint
    if load_model:
        _, target_predictor, _, _, _, _ = load_checkpoint(
            device=device,
            r_path=agent_target_load_path,
            predictor=target_predictor)



    start_end_img_path, num_image = operate_ptz_with_agent(args, actions, target_encoder, transform, target_predictor, device)
    _, start_end_time = get_position_datetime_from_labels([Path(im).stem for im in start_end_img_path])
    start_end_time = [atime.strftime(timefmt) for atime in start_end_time]
    if "start_end" not in restart_info["images"].keys():
        restart_info["images"]["start_end"] = []
        restart_info["images"]["num_images"] = 0
    restart_info["images"]["start_end"] += start_end_time
    restart_info["images"]["num_images"] += num_image
    with open(ag_dir / agent_name / "model_info.yaml", "w") as f:
        yaml.safe_dump(info_dict, f)
    update_progress(agent_name)
    return True


def get_last_image(directory):
    directory = Path(directory)
    all_files = [fp.stem for fp in directory.glob('*.jpg')]
    arr_pos, arr_datetime = get_position_datetime_from_labels(all_files)
    idx = np.argmax(arr_datetime)
    return Image.open(directory / f"{all_files[idx]}.jpg"), torch.tensor(arr_pos[idx])


def read_image_with_positon_from_path(impath: Union[Path, str]):
    impath = Path(impath)
    image = Image.open(impath)
    position, _ = get_position_datetime_from_labels(impath.stem)
    return image, torch.tensor(position)


def operate_ptz_with_agent(args, actions, target_encoder, transform, target_predictor, device):
    if args.camerabrand==0:
        print('Importing Hanwha')
        from source import sunapi_control as sunapi_control
    elif args.camerabrand==1:
        print('Importing Axis')
        from source import vapix_control as sunapi_control
        #from source import onvif_control as sunapi_control
    else:
        print('Not known camera brand number: ', args.camerabrand)

    iterations = args.iterations
    number_of_commands = args.movements

    try:
        Camera1 = sunapi_control.CameraControl(args.cameraip, args.username, args.password)
    except Exception as e:
        logger.error("Failed to connect to camera: %s", e)
        if args.publish_msgs:
            with Plugin() as plugin:
                plugin.publish('cannot.get.camera.from.ip', args.cameraip, timestamp=datetime.datetime.now())
                plugin.publish('cannot.get.camera.from.un', args.username, timestamp=datetime.datetime.now())
                plugin.publish('cannot.get.camera.from.pw', args.password, timestamp=datetime.datetime.now())
            

    if args.camerabrand==0:
        Camera1.absolute_control(1, 1, 1)
        time.sleep(1)
    elif args.camerabrand==1:
        Camera1.absolute_move(1, 1, 1)
        time.sleep(1)

    pan_modulation = 2
    tilt_modulation = 2
    zoom_modulation = 1

    pan_values = np.array([-5, -1, -0.1, 0, 0.1, 1, 5])
    pan_values = pan_values * pan_modulation
    tilt_values = np.array([-5, -1, -0.1, 0, 0.1, 1, 5])
    tilt_values = tilt_values * tilt_modulation
    if args.camerabrand==0:
        zoom_values = np.array([-0.2, -0.1, 0, 0.1, 0.2])
    elif args.camerabrand==1:
        zoom_values = 100*np.array([-2, -1, 0, 1, 2])

    zoom_values = zoom_values * zoom_modulation
    if args.publish_msgs:
        with Plugin() as plugin:
            plugin.publish('starting.new.image.collection.the.number.of.iterations.is', iterations)
            plugin.publish('the.number.of.images.recorded.by.iteration.is', number_of_commands)

    persis_dir, coll_dir, tmp_dir = get_dirs()
    if coll_dir.exists():
        shutil.rmtree(coll_dir)

    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    first_image_path = None
    num_image = 0
    for iteration in range(iterations):
        if args.publish_msgs:
            with Plugin() as plugin:
                plugin.publish('iteration.number', iteration)

        tmp_dir.mkdir(exist_ok=True)
        # Get first random image as a starting point
        # this would cause the error if we failed to capture the first image
        set_random_position(camera=Camera1, args=args)
        count = 0
        while count < 10:
            img_path = grab_image(camera=Camera1, args=args)
            if img_path and verify_image(img_path):
                break
            count += 1
            time.sleep(1) # to avoid jamming the network
        if count == 10:
            # it's unlikely to get the image at the last try
            raise RuntimeError("Failed to grab image after 10 attempts, agent has no starting image, has to stop!")

        positions = [grab_position(camera=Camera1, args=args)]
        cmds = []
        embeds = []
        rewards = []
        if first_image_path is None:
            first_image_path = img_path
        last_image_path = img_path
        for command in range(number_of_commands):
            # image, position = get_last_image(tmp_dir)
            image, position = read_image_with_positon_from_path(last_image_path)
            image = transform(image)
            image = image.unsqueeze(0)
            position_batch = position.unsqueeze(0).to(device, dtype=torch.float32)
            state_batch = target_encoder(image.to(device))
            with torch.no_grad():
                #next_state_values = target_predictor(state_batch, position_batch)
                # modified to find the minimum reward rather than maximum reward during inference phase
                max_next_state_indices = target_predictor(state_batch, position_batch).max(1).indices.item()
                #next_state_values = target_predictor(state_batch, position_batch).max(1).values
                next_state_values = target_predictor(state_batch, position_batch)
                # Apply softmax to convert to probabilities
                probs = F.softmax(next_state_values, dim=1)
                # Sample indices based on the probability distribution
                num_samples = 1  # Adjust as needed
                sampled_indices = torch.multinomial(probs.squeeze(), num_samples, replacement=True)

            print('next_state_values: ', next_state_values)
            print('probs: ', probs)
            #print('max_next_state_indices: ', max_next_state_indices)
            # if torch.rand([1]).item() > 0.9999:
            if torch.rand([1]).item() > 0.2:
                print('Sampled action')
                print('sampled_indices: ', sampled_indices.item())
                next_action = actions[sampled_indices.item()]
            else:
                print('Rewarded action')
                print('max_next_state_indices: ', max_next_state_indices)
                next_action = actions[max_next_state_indices]
            print('next_action: ', next_action)

            pan_modulation = 2
            tilt_modulation = 2
            if args.camerabrand==0:
                zoom_modulation = 1
            elif args.camerabrand==1:
                zoom_modulation = 100

            pan=next_action[0]*pan_modulation
            tilt=next_action[1]*tilt_modulation
            zoom=next_action[2]*zoom_modulation

            #set_random_position(camera=Camera1, args=args) ## I have to simply replace it with the decisions taken by the agent
            set_relative_position(camera=Camera1, args=args,
                                  pan=pan,
                                  tilt=tilt,
                                  zoom=zoom)
            # Make sure the image is captured before moving on
            count = 0
            while count < 10:
                img_path = grab_image(camera=Camera1, args=args)
                if img_path and verify_image(img_path):
                    break
                count += 1
                # it's unlikely to get the image at the last try
                time.sleep(1) # to avoid jamming the network
            if count == 10:
                logger.warning("Failed to grab image after 10 attempts, skip this command")
                if os.path.exists(img_path):
                    os.remove(img_path)
                continue
            positions.append(grab_position(camera=Camera1, args=args))
            cmds.append(f"{pan:.2f},{tilt:.2f},{zoom:.2f}")
            embeds.append(state_batch.detach().cpu())
            rewards.append(next_state_values.detach().cpu())
            last_image_path = img_path
        #publish_images()
        num_image += collect_images(args.keepimages)
        
        shutil.rmtree(tmp_dir)
        cur_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S.%f")
        if args.trackpositions or args.track_all:
            collect_positions(positions, cur_time)
            collect_commands(cmds, cur_time)
        
        if args.track_all:
            collect_embeds_rewards(embeds, rewards, cur_time)
    return [first_image_path, last_image_path], num_image

def run(args, fname, mode):

    logger.info('called-params %s', fname)

    # -- load script params
    params = None
    with open(fname, 'r') as y_file:
        logger.info('loading params...')
        params = yaml.safe_load(y_file)
        logger.info('loaded params...')
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(params)

    if mode=='navigate_env':
        return control_ptz(args, params)
    else:
        raise ValueError(f"Unexpected mode {mode}")

# Fix for ValueError: num_samples=0 Error

This error indicates a dataset initialization problem where your code is trying to create a dataloader with zero samples. Here's how to fix it:

## Cause

This typically happens in one of these scenarios:
1. No images were collected during the preparation stage
2. The dataset directory path is incorrect
3. Permission issues accessing image files

## Solution

Add checks to prevent loading empty datasets:

```python
# Find where the DataLoader is created

# BEFORE the code creates a DataLoader, add this check:
if len(dataset) == 0:
    logger.error("Dataset contains 0 samples! Check image collection and storage paths.")
    logger.info("Attempting to recollect images...")
    
    # Force image recollection
    from source.prepare_dataset import get_images_from_storage, prepare_images
    get_images_from_storage(args)
    prepare_images()
    
    # Try recreating dataset
    dataset = PTZDataset(...)  # Recreate with same parameters
    
    if len(dataset) == 0:
        logger.error("Still no images available after recollection. Using fallback images.")
        # Use any fallback/sample images if available
        fallback_dir = "/persistence/sample_images"
        if os.path.exists(fallback_dir) and len(os.listdir(fallback_dir)) > 0:
            # Create dataset with fallback images
            dataset = PTZDataset(root=fallback_dir, ...)
        else:
            logger.critical("No images available and no fallbacks. Cannot proceed.")
            return False  # Signal that training couldn't complete

# Then proceed with creating the DataLoader only if dataset has samples
if len(dataset) > 0:
    dataloader = DataLoader(dataset, ...)
else:
    return False  # Cannot proceed without data
```

## Additional Check in Dataset Classes

Also modify the dataset classes to handle empty directories:

```python
class PTZDataset(Dataset):
    def __init__(self, root, ...):
        # Existing initialization code...
        
        # Add this check after file list is created
        if len(self.files) == 0:
            logger.warning(f"No image files found in {root}. Check path and permissions.")
            # Don't raise error here, let the higher level code handle it
```

This solution adds resilience to the code by detecting empty datasets, attempting to recollect images, and providing clear error messages when the process fails.
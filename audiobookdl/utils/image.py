"""
Image processing utilities for cover art normalization
"""
import io
from typing import Optional, Tuple
from PIL import Image
from audiobookdl import logging

# Maximum dimensions for cover images (prevents display issues in some audiobook apps)
MAX_COVER_SIZE = 1400  # pixels (width or height)


def detect_image_format(image_data: bytes) -> Optional[str]:
    """
    Detect actual image format from magic bytes

    :param image_data: Raw image bytes
    :returns: Format string ('jpeg', 'png', 'gif', 'webp') or None
    """
    if image_data.startswith(b'\xff\xd8\xff'):
        return 'jpeg'
    elif image_data.startswith(b'\x89PNG'):
        return 'png'
    elif image_data.startswith(b'GIF'):
        return 'gif'
    elif image_data.startswith(b'RIFF') and len(image_data) > 12 and image_data[8:12] == b'WEBP':
        return 'webp'
    return None


def normalize_cover_image(image_data: bytes, declared_format: str) -> Tuple[bytes, str]:
    """
    Normalize cover image for better compatibility with audiobook applications.

    This function:
    - Detects the actual image format (may differ from declared format)
    - Converts WebP and other formats to JPEG (some apps don't support WebP in M4B)
    - Resizes oversized images that might cause display issues
    - Handles transparency by compositing on white background
    - Optimizes image quality and file size

    :param image_data: Raw image bytes
    :param declared_format: Format claimed by the source (e.g., 'jpg', 'png', 'webp')
    :returns: Tuple of (normalized_image_data, actual_format)
    """
    if not image_data:
        return image_data, declared_format

    try:
        # Detect actual format from magic bytes
        detected_format = detect_image_format(image_data)
        if detected_format:
            logging.debug(f"Cover image: declared as '{declared_format}', detected as '{detected_format}'")

        # Open image with PIL
        img = Image.open(io.BytesIO(image_data))
        original_format = img.format
        original_size = img.size
        logging.debug(f"Cover image info: format={original_format}, mode={img.mode}, size={original_size}")

        # Check if image needs processing
        needs_resize = max(img.size) > MAX_COVER_SIZE
        is_jpeg = img.format in ('JPEG', 'JPG')
        has_transparency = img.mode in ('RGBA', 'LA', 'P')

        if not needs_resize and is_jpeg and not has_transparency:
            # Image is already in good format, return as-is
            logging.debug("Cover image is already optimized, using as-is")
            return image_data, 'jpg'

        # Process image
        if needs_resize:
            # Calculate new size maintaining aspect ratio
            ratio = MAX_COVER_SIZE / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            logging.debug(f"Resizing cover from {original_size} to {new_size}")
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to RGB if needed (removes transparency, required for JPEG)
        if img.mode != 'RGB':
            logging.debug(f"Converting image mode from {img.mode} to RGB")
            # If image has transparency, composite it on white background
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                else:
                    background.paste(img, mask=img.split()[-1])
                img = background
            else:
                img = img.convert('RGB')

        # Save as optimized JPEG
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=90, optimize=True)
        normalized_data = output.getvalue()

        original_size_kb = len(image_data) / 1024
        new_size_kb = len(normalized_data) / 1024
        logging.debug(f"Cover image normalized: {original_size_kb:.1f} KB -> {new_size_kb:.1f} KB")

        return normalized_data, 'jpg'

    except Exception as e:
        # If processing fails, return original image
        logging.debug(f"Failed to normalize cover image: {e}. Using original.")
        return image_data, declared_format

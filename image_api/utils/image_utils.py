def calculate_width(image, target_height):
    original_height = image.height
    original_width = image.width
    aspect_ratio = original_width / original_height

    target_height = int(target_height)
    calculated_width = int(target_height * aspect_ratio)

    return calculated_width

from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_image(filename, size=(1920, 1080), bg_color=(70, 130, 180), text="Placeholder"):
    """Create a placeholder image with text."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Create image with background color
    image = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(image)
    
    # Calculate text size and position
    font_size = min(size) // 10
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    text_width = draw.textlength(text, font=font)
    text_height = font_size
    text_x = (size[0] - text_width) // 2
    text_y = (size[1] - text_height) // 2
    
    # Draw text
    draw.text((text_x, text_y), text, fill='white', font=font)
    
    # Save image
    image.save(filename, 'JPEG', quality=90)

def main():
    # Set base directory for static files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_dir = os.path.join(base_dir, 'static', 'images')
    
    # Create hero background
    create_placeholder_image(
        os.path.join(static_dir, 'hero-bg.jpg'),
        size=(1920, 1080),
        bg_color=(45, 62, 80),  # Dark blue
        text="Dance Competition Hero"
    )
    
    # Create testimonial images
    for i in range(1, 4):
        create_placeholder_image(
            os.path.join(static_dir, f'testimonial{i}.jpg'),
            size=(200, 200),
            bg_color=(70, 130, 180),  # Steel blue
            text=f"Testimonial {i}"
        )

if __name__ == "__main__":
    main()
    print("Placeholder images generated successfully!")

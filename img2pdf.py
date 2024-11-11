from PIL import Image

# Open the PNG image
image = Image.open('image.jpg')

# Convert to RGB (necessary for PNG with transparency)
if image.mode == 'RGBA':
    image = image.convert('RGB')

# Save the image as a PDF
image.save('output.pdf')

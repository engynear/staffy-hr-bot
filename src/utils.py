from PIL import Image, ImageDraw, ImageFont
import io
import emoji

def draw_text_with_emojis(draw, position, text, normal_font, emoji_font, fill=(0, 0, 0)):
    # Initial position
    x, y = position
    
    # Split text into individual characters or emojis
    parts = [char if char.isalnum() or len(char) > 1 else emoji.demojize(char) for char in text]
    buffer = ''
    for part in parts:
        if ":" in part:  # This is an emoji
            if buffer:  # If we have accumulated some text, draw it first
                draw.text((x, y), buffer, font=normal_font, fill=fill)
                x += normal_font.getmask(buffer).getbbox()[2]
                buffer = ''  # Clear the buffer
            # Convert the emoji code to the actual emoji character
            char = emoji.emojize(part)
            draw.text((x, y), char, font=emoji_font, fill=fill)
            x += emoji_font.getmask(char).getbbox()[2]
        else:
            buffer += part
    if buffer:  # After the loop, check if we still have some remaining text in the buffer and draw it
        draw.text((x, y), buffer, font=normal_font, fill=fill)

def draw_text_with_emojis_in_box(draw, box, text, normal_font, emoji_font, fill=(0, 0, 0)):
    x, y, max_x, max_y = box
    width = max_x - x

    words = text.split()
    buffer = ''
    for word in words:
        # Проверим, является ли слово эмодзи
        if ':' in word:
            emoji_word = emoji.emojize(word)
            word_width = emoji_font.getmask(emoji_word).getbbox()[2]
        else:
            word_width = normal_font.getmask(word).getbbox()[2]

        # Если текущая ширина буфера плюс ширина слова превышает максимальную ширину, 
        # выводим буфер на изображение и начинаем новую строку
        if x + word_width > max_x or "\n" in word:
            draw.text((x, y), buffer, font=normal_font, fill=fill)
            buffer = ''
            x = box[0]
            y += normal_font.getmask(word).getbbox()[3]
            if y > max_y:
                break  # Если превысили максимальную высоту, завершаем работу

        buffer += word + ' '
        x += word_width + normal_font.getmask(word).getbbox()[2]  # Ширина пробела

    if buffer and y <= max_y:
        draw.text((x, y), buffer, font=normal_font, fill=fill)


async def wish_to_image(from_user, to_user, wish: str):
    image = Image.open('src/assets/template.png')
    draw = ImageDraw.Draw(image)

    normal_font = ImageFont.truetype('src/assets/Roboto.ttf', size=28, encoding='utf-8')
    emoji_font = ImageFont.truetype('src/assets/segoi.ttf', size=28, encoding='utf-8')

    draw_text_with_emojis(draw, (110, 278), f'{from_user["name"]}', normal_font, emoji_font, fill=(0, 0, 255))
    draw_text_with_emojis(draw, (110, 328), f'{to_user["name"]}', normal_font, emoji_font, fill=(0, 0, 255))
    draw_text_with_emojis_in_box(draw, (485, 100, 900, 500), wish, normal_font, emoji_font, fill=(0, 0, 255))

    buffer = io.BytesIO()
    image.save(buffer, 'PNG')
    buffer.seek(0)

    #show image
    image.show()
    return buffer

import asyncio

asyncio.run(wish_to_image({'name': 'Вова'}, {'name': 'Паша'}, '''
    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
    Nulla facilisi. Sed sit amet tortor sed magna euismod
    ❤️
🐾
    tincidunt. Nulla facilisi. Sed sit amet tortor sed magna
''' ))

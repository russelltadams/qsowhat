import os
import json
from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont  # Import Pillow modules
import datetime  # Import the datetime module

app = Flask(__name__)

# Configuration
JSON_FILES_DIR = 'qso_data'  # Directory where your pre-generated JSON files are stored
QSO_CARDS_DIR = 'qso_cards'  # Directory where generated QSO card images will be saved
TEMPLATE_IMAGE_PATH = 'static/qso_card_template.png'  # Path to your base image template
# Ensure directories exist
os.makedirs(JSON_FILES_DIR, exist_ok=True)
os.makedirs(QSO_CARDS_DIR, exist_ok=True)


def load_qso_data(callsign):
    """
    Loads QSO data from a JSON file for a given callsign.

    Args:
        callsign (str): The callsign to load data for.

    Returns:
        list: A list of QSO dictionaries, or None if the file doesn't exist or on error.
    """
    json_file_path = os.path.join(JSON_FILES_DIR, f'{callsign.upper()}.json')
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"JSON file not found for callsign {callsign}")
        return None
    except Exception as e:
        print(f"Error loading JSON data: {e}")
        return None


def generate_qso_card(qso_data, my_callsign, other_callsign):
    """
    Generates a QSO card image using Pillow.  Handles file creation and
    checks for existing files.

    Args:
        qso_data (dict): A dictionary containing QSO data.
        my_callsign (str): Your callsign.
        other_callsign (str): The other station's callsign.

    Returns:
        str: The URL of the generated QSO card image, or None on error.
    """

    # Construct the filename.
    qso_date_str = qso_data.get('qso_date')  # Get date
    qso_time_str = qso_data.get('time_on')  # Get time
    if not qso_date_str or not qso_time_str:
        print("Error: QSO Date or Time is missing")
        return None
    try:
        #  Attempt to parse the date and time.  Handle different formats.
        qso_datetime = None
        formats_to_try = ["%Y%m%d %H%M%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H%M%S"]  # Add more if needed
        for fmt in formats_to_try:
            try:
                qso_datetime = datetime.datetime.strptime(
                    f"{qso_date_str} {qso_time_str}", fmt
                )
                break  # If successful, break the loop
            except ValueError:
                pass  # If this format fails, try the next one

        if qso_datetime is None:
            print(
                "Error: Could not parse date/time with any of the expected formats."
            )
            print(f"qso_date_str: {qso_date_str}, qso_time_str: {qso_time_str}")
            return None

        filename = (
            f"qso_{qso_datetime.strftime('%Y%m%d_%H%M%S')}_"
            f"{my_callsign.upper()}_{other_callsign.upper()}.png"
        )
    except ValueError as e:
        print(f"Error formatting date/time: {e}")
        return None

    image_path = os.path.join(QSO_CARDS_DIR, filename)
    image_url = f'/qso_cards/{filename}'  # URL for the template
    print(f"generate_qso_card - image_path: {image_path}")  # Debugging print
    print(f"generate_qso_card - image_url: {image_url}")  # Debugging print

    if os.path.exists(image_path):
        print(f"QSO card already exists: {image_path}")
        return image_url  # Return the URL if the image already exists

    try:
        # Load the template image
        print(f"generate_qso_card - Attempting to open image: {TEMPLATE_IMAGE_PATH}")  # Debug
        template_image = Image.open(TEMPLATE_IMAGE_PATH)
        print("generate_qso_card - Image opened successfully")  # Debug
        draw = ImageDraw.Draw(template_image)
        print("generate_qso_card - ImageDraw created")  # Debug

        # Use a font.  You'll need to provide a font file.
        font_path = "arial.ttf"  # Replace with the actual path to your font file
        if not os.path.exists(font_path):
            print(
                f"generate_qso_card - Error: Font file not found at {font_path}.  Using default font."
            )
            font = ImageFont.load_default()
            print("generate_qso_card - Default font loaded")  # Debug
        else:
            font = ImageFont.truetype(font_path, 20)  # Adjust font size as needed
            print("generate_qso_card - Custom font loaded")  # Debug

        # Define text positions (adjust these based on your template)
        call_pos = (100, 50)
        date_pos = (100, 80)
        time_pos = (100, 110)
        mode_pos = (100, 140)
        band_pos = (100, 170)

        # Draw the text onto the image
        draw.text(
            call_pos, f"Call: {qso_data.get('call', 'N/A')}", font=font, fill=(0, 0, 0)
        )
        print("generate_qso_card - Callsign text drawn")  # Debug
        draw.text(
            date_pos, f"Date: {qso_data.get('qso_date', 'N/A')}", font=font, fill=(0, 0, 0)
        )
        print("generate_qso_card - Date text drawn")  # Debug
        draw.text(
            time_pos, f"Time: {qso_data.get('time_on', 'N/A')}", font=font, fill=(0, 0, 0)
        )
        print("generate_qso_card - Time text drawn")  # Debug
        draw.text(
            mode_pos, f"Mode: {qso_data.get('mode', 'N/A')}", font=font, fill=(0, 0, 0)
        )
        print("generate_qso_card - Mode text drawn")  # Debug
        draw.text(
            band_pos, f"Band: {qso_data.get('band', 'N/A')}", font=font, fill=(0, 0, 0)
        )
        print("generate_qso_card - Band text drawn")  # Debug

        # Save the image
        template_image.save(image_path, 'PNG')
        print(f"generate_qso_card - QSO card generated: {image_path}")
        return image_url
    except Exception as e:
        print(f"generate_qso_card - Error generating QSO card: {e}")
        return None


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles the main page, including the search form.
    """
    if request.method == 'POST':
        callsign = request.form.get('callsign')
        if not callsign:
            return render_template(
                'index.html', error_message="Please enter a callsign."
            )

        log_data = load_qso_data(callsign)  # Load the JSON data
        if not log_data:
            return render_template(
                'index.html',
                error_message=f"No contacts found for callsign {callsign}.",
            )

        # Add qso_card_url to each contact in log_data
        for i, contact in enumerate(log_data):
            #  Get the other callsign.
            other_call = contact.get('call', 'Unknown')
            my_call = contact.get('station_callsign', 'Unknown')  # added station callsign
            contact['qso_card_url'] = (
                f"/qso_card/{callsign}/{i}"
            )  # changed this line
        return render_template('index.html', callsign=callsign, log_data=log_data)
    return render_template('index.html')


@app.route('/qso_cards/<filename>')
def serve_qso_card(filename):
    """
    Serves the generated QSO card image.  This route is needed to make the URLs work.

    Args:
        filename (str): The name of the image file.

    Returns:
        File: The image file.
    """
    image_path = os.path.join(QSO_CARDS_DIR, filename)
    print(f"serve_qso_card - image_path: {image_path}")  # Debugging print
    if not os.path.exists(image_path):
        return "Image not found", 404
    return send_file(image_path, mimetype='image/png')  # Set the correct MIME type


@app.route('/qso_card/<callsign>/<int:contact_index>')  # added route
def qso_card(callsign, contact_index):
    """
    Generates a QSO card image and returns the rendered HTML.

    Args:
        callsign (str): The callsign of the station.
        contact_index (int): The index of the contact in the JSON data.

    Returns:
        str:  The rendered HTML
             or an error message.
    """
    log_data = load_qso_data(callsign)
    if not log_data:
        return f'No data found for callsign {callsign}', 404

    if not 0 <= contact_index < len(log_data):
        return f'Invalid contact index {contact_index} for callsign {callsign}', 400

    qso_data = log_data[contact_index]
    my_call = qso_data.get('station_callsign', 'Unknown')
    other_call = qso_data.get('call', 'Unknown')
    image_url = generate_qso_card(qso_data, my_call, other_call)  # Generate the card
    print(f"qso_card route - image_url: {image_url}")  # Debug

    if image_url:
        return send_file(os.path.join(QSO_CARDS_DIR, image_url.split('/')[-1]), mimetype='image/png')  # Serve the image
    else:
        return 'Failed to generate QSO card', 500


if __name__ == '__main__':
    app.run(debug=True)

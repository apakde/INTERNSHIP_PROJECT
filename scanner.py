from flask import Flask, render_template, request, jsonify, send_file
import cv2
import numpy as np
import os
import utlis
import hdbcli.dbapi
import io
from flask_cors import CORS

# Initialize SAP HANA connection
HANA_HOST = "d0afe0ae-62c8-40ef-a998-b83ca6c5f30e.hana.trial-us10.hanacloud.ondemand.com"
HANA_PORT = 443
HANA_USER = "DBADMIN"  # Replace with your actual DB user
HANA_PASSWORD = "Apakde@sap03"  # Replace with your actual password

# Establish connection
conn = hdbcli.dbapi.connect(
    address=HANA_HOST,
    port=HANA_PORT,
    user=HANA_USER,
    password=HANA_PASSWORD,
    encrypt=True,
    sslValidateCertificate=False
)
cursor = conn.cursor()

utlis.initializeTrackbars()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    if 'image' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})
    
    # Read file and process it
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    processed_img = process_image(img)
    
    # Convert processed image to bytes for storage
    _, processed_buffer = cv2.imencode('.png', processed_img)
    processed_bytes = processed_buffer.tobytes()
    
    # Store in SAP HANA Cloud
    cursor.execute(
        "INSERT INTO SCANNED_DOCUMENTS (FILENAME, FILETYPE, FILEDATA) VALUES (?, ?, ?)",
        (file.filename, 'image/png', processed_bytes)
    )
    conn.commit()

    return jsonify({'message': 'File uploaded and stored successfully!'})

def process_image(img):
    """Process the image to make it look like a scanned document."""
    height, width = 480, 600
    img = cv2.resize(img, (width, height))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 1)
    thres = utlis.valTrackbars()
    thresholds = cv2.Canny(blur, thres[0], thres[1])
    kernels = np.ones((5, 5))
    dilate = cv2.dilate(thresholds, kernels, iterations=2)
    thresholds = cv2.erode(dilate, kernels, iterations=1)

    contours, _ = cv2.findContours(thresholds, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest, area = utlis.biggestContour(contours)
    if largest.size != 0:
        largest = utlis.reorder(largest)
        pt1 = np.float32(largest)
        pt2 = np.float32([[0, 0], [width, 0], [0, height], [width, height]])
        matrix = cv2.getPerspectiveTransform(pt1, pt2)
        WarpColored = cv2.warpPerspective(img, matrix, (width, height))
        imgGray = cv2.cvtColor(WarpColored, cv2.COLOR_BGR2GRAY)
        return imgGray
    return img

@app.route('/documents', methods=['GET'])
def get_documents():
    """Retrieve stored scanned documents from SAP HANA Cloud."""
    cursor.execute("SELECT ID, FILENAME FROM SCANNED_DOCUMENTS")
    documents = cursor.fetchall()
    return jsonify([{"id": row[0], "filename": row[1]} for row in documents])

@app.route('/document/<int:doc_id>', methods=['GET'])
def get_document(doc_id):
    """Fetch a specific document from SAP HANA Cloud."""
    cursor.execute("SELECT FILEDATA, FILETYPE FROM SCANNED_DOCUMENTS WHERE ID = ?", (doc_id,))
    result = cursor.fetchone()
    
    if not result:
        return jsonify({"error": "Document not found"}), 404
    
    file_data, file_type = result
    return send_file(io.BytesIO(file_data), mimetype=file_type, as_attachment=True, download_name=f"document_{doc_id}.png")

if __name__ == '__main__':
    app.run(debug=True)

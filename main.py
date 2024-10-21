from flask import Flask, request, send_file
import requests
import ezdxf
import svgwrite
import os

app = Flask(__name__)

def dxf_to_svg(dxf_file_path, svg_file_path):
    """DXF dosyasını SVG'ye dönüştürür."""
    doc = ezdxf.readfile(dxf_file_path)
    dwg = svgwrite.Drawing(svg_file_path, profile='tiny')

    # Çizgiler
    for entity in doc.modelspace().query('LINE'):
        start = entity.dxf.start
        end = entity.dxf.end
        dwg.add(dwg.line(start=(start.x, start.y), end=(end.x, end.y), stroke=svgwrite.rgb(0, 0, 0, '%')))

    # Daireler
    for entity in doc.modelspace().query('CIRCLE'):
        center = entity.dxf.center
        radius = entity.dxf.radius
        dwg.add(dwg.circle(center=(center.x, center.y), r=radius, stroke=svgwrite.rgb(0, 0, 0, '%'), fill='none'))

    # Yarım Daireler (Arc)
    for entity in doc.modelspace().query('ARC'):
        center = entity.dxf.center
        radius = entity.dxf.radius
        start_angle = entity.dxf.start_angle
        end_angle = entity.dxf.end_angle
        start_point = (center.x + radius * cos(radians(start_angle)), center.y + radius * sin(radians(start_angle)))
        end_point = (center.x + radius * cos(radians(end_angle)), center.y + radius * sin(radians(end_angle)))
        dwg.add(dwg.path(d="M{} {} A{} {} 0 0 1 {} {}".format(center.x, center.y, radius, radius, end_point[0], end_point[1]),
                         stroke=svgwrite.rgb(0, 0, 0, '%'), fill='none'))

    # Çokgenler
    for entity in doc.modelspace().query('LWPOLYLINE'):
        points = [(point.x, point.y) for point in entity.get_points()]
        dwg.add(dwg.polygon(points, stroke=svgwrite.rgb(0, 0, 0, '%'), fill='none'))

    # Metin
    for entity in doc.modelspace().query('TEXT'):
        insert = entity.dxf.insert
        text = entity.dxf.text
        dwg.add(dwg.text(text, insert=(insert.x, insert.y), fill='black'))

    dwg.save()

@app.route('/convert', methods=['POST'])
def convert_dxf_to_svg():
    # DXF dosyasının URL'sini al
    dxf_url = request.json.get('url')

    # Dosyayı indir
    response = requests.get(dxf_url)
    dxf_file_path = 'temp.dxf'

    with open(dxf_file_path, 'wb') as f:
        f.write(response.content)

    # DXF dosyasını SVG'ye dönüştür
    svg_file_path = 'output.svg'
    dxf_to_svg(dxf_file_path, svg_file_path)

    # Geçici dosyaları temizle
    os.remove(dxf_file_path)

    # SVG dosyasını gönder
    return send_file(svg_file_path, mimetype='image/svg+xml')

if __name__ == '__main__':
    app.run(debug=True)
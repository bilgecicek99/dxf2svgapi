from flask import Flask, request, send_file
import requests
import ezdxf
import svgwrite
import os
from math import cos, sin, radians
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Tüm kaynaklara izin ver. Eğer belirli bir alanı hedeflemek isterseniz, yukarıdaki örnekteki gibi değiştirebilirsiniz.

def dxf_to_svg(dxf_file_path, svg_file_path):
    """DXF dosyasını SVG'ye dönüştürür."""
    doc = ezdxf.readfile(dxf_file_path)
    dwg = svgwrite.Drawing(svg_file_path, profile='tiny')

    # Çizgiler
    for entity in doc.modelspace().query('LINE'):
        start = entity.dxf.start
        end = entity.dxf.end
        dwg.add(dwg.line(start=(start.x, start.y), end=(end.x, end.y),
                         stroke=svgwrite.rgb(0, 0, 0, '%')))

    # Daireler
    for entity in doc.modelspace().query('CIRCLE'):
        center = entity.dxf.center
        radius = entity.dxf.radius
        dwg.add(dwg.circle(center=(center.x, center.y), r=radius,
                           stroke=svgwrite.rgb(0, 0, 0, '%'), fill='none'))

    # Yarım Daireler (Arc)
    for entity in doc.modelspace().query('ARC'):
        center = entity.dxf.center
        radius = entity.dxf.radius
        start_angle = entity.dxf.start_angle
        end_angle = entity.dxf.end_angle

        # Başlangıç ve bitiş noktalarını hesapla
        start_x = center.x + radius * cos(radians(start_angle))
        start_y = center.y + radius * sin(radians(start_angle))
        end_x = center.x + radius * cos(radians(end_angle))
        end_y = center.y + radius * sin(radians(end_angle))

        # SVG yay yolu oluştur
        large_arc_flag = '1' if abs(end_angle - start_angle) > 180 else '0'
        sweep_flag = '1' if end_angle > start_angle else '0'

        path_d = f"M {start_x} {start_y} A {radius} {radius} 0 {large_arc_flag} {sweep_flag} {end_x} {end_y}"
        dwg.add(dwg.path(d=path_d, stroke=svgwrite.rgb(0, 0, 0, '%'), fill='none'))

    # Çokgenler
    for entity in doc.modelspace().query('LWPOLYLINE'):
        points = [(point.x, point.y) for point in entity.get_points()]
        dwg.add(dwg.polygon(points, stroke=svgwrite.rgb(0, 0, 0, '%'),
                            fill='none'))

    # Metin
    for entity in doc.modelspace().query('TEXT'):
        insert = entity.dxf.insert
        text = entity.dxf.text
        dwg.add(dwg.text(text, insert=(insert.x, insert.y), fill='black'))

    dwg.save()


@app.route('/convert', methods=['POST'])
def convert_dxf_to_svg():
    try:
        # DXF dosyasının URL'sini al
        dxf_url = request.json.get('url')
        if not dxf_url:
            return {'error': 'URL is required'}, 400

        # Dosyayı indir
        response = requests.get(dxf_url)
        if response.status_code != 200:
            return {'error': 'Failed to download DXF file'}, 400

        dxf_file_path = 'temp.dxf'
        svg_file_path = 'output.svg'

        # Dosyayı kaydet
        with open(dxf_file_path, 'wb') as f:
            f.write(response.content)

        # DXF dosyasını SVG'ye dönüştür
        dxf_to_svg(dxf_file_path, svg_file_path)

        # Geçici DXF dosyasını temizle
        os.remove(dxf_file_path)

        # SVG dosyasını gönder
        return send_file(svg_file_path, mimetype='image/svg+xml')

    except Exception as e:
        return {'error': str(e)}, 500

    finally:
        # Temizlik işlemleri
        if os.path.exists(dxf_file_path):
            os.remove(dxf_file_path)
        if os.path.exists(svg_file_path):
            os.remove(svg_file_path)


if __name__ == '__main__':
    app.run(debug=True)

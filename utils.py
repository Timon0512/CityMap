import os
import io
import base64
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
from maptoposter import create_map_poster as map
import osmnx as ox
from matplotlib.font_manager import FontProperties

def get_or_create_thumbnail(original_path):
    # Pfad für das Thumbnail definieren (z.B. im Unterordner /thumbnails)
    folder, filename = os.path.split(original_path)
    thumb_folder = os.path.join(folder, "thumbs")
    print(thumb_folder)

    if not os.path.exists(thumb_folder):
        os.makedirs(thumb_folder)

    thumb_path = os.path.join(thumb_folder, f"thumb_{filename}")
    print(thumb_path)

    # Nur erstellen, wenn es noch nicht existiert
    if not os.path.exists(thumb_path):
        with Image.open(original_path) as img:
            img.thumbnail((300, 300))
            img.save(thumb_path, "PNG")

    return thumb_path

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded_string}"
    except Exception as e:
        print(e)
        return None


def plot_everything(G, water, parks, THEME, city, country, point):
    fig, ax = plt.subplots(figsize=(12, 16), facecolor=THEME['bg'])
    ax.set_facecolor(THEME['bg'])
    ax.set_position([0, 0, 1, 1])

    # Layer 1: Polygons
    if water is not None and not water.empty:
        water.plot(ax=ax, facecolor=THEME['water'], edgecolor='none', zorder=1)
    if parks is not None and not parks.empty:
        parks.plot(ax=ax, facecolor=THEME['parks'], edgecolor='none', zorder=2)

    # Layer 2: Roads with hierarchy coloring
    print("Applying road hierarchy colors...")
    edge_colors = map.get_edge_colors_by_type(G)
    edge_widths = map.get_edge_widths_by_type(G)

    ox.plot_graph(
        G, ax=ax, bgcolor=THEME['bg'],
        node_size=0,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        show=False, close=False
    )

    # Layer 3: Gradients (Top and Bottom)
    map.create_gradient_fade(ax, THEME['gradient_color'], location='bottom', zorder=10)
    map.create_gradient_fade(ax, THEME['gradient_color'], location='top', zorder=10)

    # 4. Typography using Roboto font
    FONTS = map.FONTS
    if FONTS:
        font_main = FontProperties(fname=FONTS['bold'], size=60)
        font_top = FontProperties(fname=FONTS['bold'], size=40)
        font_sub = FontProperties(fname=FONTS['light'], size=22)
        font_coords = FontProperties(fname=FONTS['regular'], size=14)
    else:
        # Fallback to system fonts
        font_main = FontProperties(family='monospace', weight='bold', size=60)
        font_top = FontProperties(family='monospace', weight='bold', size=40)
        font_sub = FontProperties(family='monospace', weight='normal', size=22)
        font_coords = FontProperties(family='monospace', size=14)

    spaced_city = "  ".join(list(city.upper()))

    # --- BOTTOM TEXT ---
    ax.text(0.5, 0.14, spaced_city, transform=ax.transAxes,
            color=THEME['text'], ha='center', fontproperties=font_main, zorder=11)

    ax.text(0.5, 0.10, country.upper(), transform=ax.transAxes,
            color=THEME['text'], ha='center', fontproperties=font_sub, zorder=11)

    lat, lon = point
    coords = f"{lat:.4f}° N / {lon:.4f}° E" if lat >= 0 else f"{abs(lat):.4f}° S / {lon:.4f}° E"
    if lon < 0:
        coords = coords.replace("E", "W")

    ax.text(0.5, 0.07, coords, transform=ax.transAxes,
            color=THEME['text'], alpha=0.7, ha='center', fontproperties=font_coords, zorder=11)

    ax.plot([0.4, 0.6], [0.125, 0.125], transform=ax.transAxes,
            color=THEME['text'], linewidth=1, zorder=11)


    # 5. Save
    # print(f"Saving to {output_file}...")
    # plt.savefig(output_file, dpi=300, facecolor=THEME['bg'])
    # plt.close()
    # print(f"✓ Done! Poster saved as {output_file}")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=300, facecolor=THEME['bg'])
    plt.close()
    buf.seek(0)
    return buf

#
# poster_folder = r"C:\Users\Timon\PycharmProjects\CityMap2\maptoposter\posters"
#
# # Liste alle Dateien im Ordner auf
# for dateiname in os.listdir(poster_folder):
#     # Nur PNG-Dateien verarbeiten (keine Ordner oder andere Dateien)
#     if dateiname.lower().endswith(".png"):
#         voller_pfad = os.path.join(poster_folder, dateiname)
#
#         # Funktion aufrufen
#         thumb_pfad = get_or_create_thumbnail(voller_pfad)
#         print(f"Thumbnail erstellt/geprüft für: {dateiname} -> {thumb_pfad}")

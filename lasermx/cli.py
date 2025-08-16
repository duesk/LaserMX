import argparse, sys, time
from .drivers.grbl_serial import GrblSerialDriver
from .pipeline.svg_loader import load_svg_as_polylines
from .pipeline.dxf_loader import load_dxf_as_polylines
from .pipeline.gcode_generator import polylines_to_gcode, save_gcode
from .utils.serial_utils import list_serial_ports

def main(argv=None):
    parser = argparse.ArgumentParser(description="LaserMX CLI")
    parser.add_argument("--list", action="store_true", help="Listar puertos seriales y salir.", default=False)
    parser.add_argument("--port", help="Puerto serial (e.g., /dev/tty.usbserial-XXXX).")
    parser.add_argument("--baud", type=int, default=115200, help="Baudios (default 115200).")
    parser.add_argument("--cmd", help="Enviar un comando GRBL y salir.")
    parser.add_argument("--file", help="Archivo SVG o DXF a convertir.")
    parser.add_argument("--to-gcode", help="Ruta de salida para G-code.")
    parser.add_argument("--run", action="store_true", help="Enviar el G-code al controlador tras convertir.")
    args = parser.parse_args(argv)

    if args.list:
        for p in list_serial_ports():
            print(p)
        return 0

    drv = GrblSerialDriver(on_line=lambda s: print(s))
    if args.port:
        drv.connect(args.port, args.baud)

    if args.cmd:
        if not args.port:
            print("Debe especificar --port para enviar comandos.", file=sys.stderr); return 2
        drv.send_command(args.cmd); time.sleep(0.5); drv.disconnect(); return 0

    if args.file:
        if args.file.lower().endswith(".svg"):
            polys = load_svg_as_polylines(args.file)
        elif args.file.lower().endswith(".dxf"):
            polys = load_dxf_as_polylines(args.file)
        else:
            print("Extensión no soportada. Use .svg o .dxf", file=sys.stderr); return 2
        g = polylines_to_gcode(polys)
        if args.to_gcode:
            save_gcode(g, args.to_gcode); print(f"G-code guardado en {args.to_gcode}")
        if args.run:
            if not args.port:
                print("Debe especificar --port para --run", file=sys.stderr); return 2
            drv.stream_gcode(g)
            time.sleep(0.2)
        if args.port:
            drv.disconnect()
        return 0

    parser.print_help(); return 0

if __name__ == "__main__":
    raise SystemExit(main())
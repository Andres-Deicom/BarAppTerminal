import sys
import os
import requests
import curses
from flask import Blueprint

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

api = Blueprint('api', __name__)

BASE_URL = "http://localhost:3000/api"

def get_request(endpoint):
    response = requests.get(BASE_URL + endpoint)
    return response.json()

def post_request(endpoint, data):
    response = requests.post(BASE_URL + endpoint, json=data)
    return response.json()

def show_menu(stdscr, selected_index):
    stdscr.clear()
    menu_items = ["Ver mesas", "Ver pedidos en preparación", "Vaciar mesa", "Cambiar estado del pedido", "Salir"]
    stdscr.addstr("Bienvenido al sistema de gestión de restaurante:\n")
    for index, item in enumerate(menu_items):
        if index == selected_index:
            stdscr.addstr(f"{index + 1}. {item}\n", curses.color_pair(1))
        else:
            stdscr.addstr(f"{index + 1}. {item}\n")
    stdscr.refresh()

def show_mesas(stdscr, mesas, selected_index, only_occupied=False): 
    stdscr.clear()
    stdscr.addstr("Mesas disponibles:\n")
    for i, mesa in enumerate(mesas):
        if only_occupied and not mesa['ocupada']:
            continue
        if i == selected_index:
            stdscr.addstr(f"Mesa {mesa['capacidad']}: {'Ocupada' if mesa['ocupada'] else 'Libre'}\n", curses.color_pair(1))
        else:
            stdscr.addstr(f"Mesa {mesa['capacidad']}: {'Ocupada' if mesa['ocupada'] else 'Libre'}\n")
    stdscr.addstr("\nUtilice las flechas arriba y abajo para seleccionar una mesa, luego presione 'Enter'. 'q' para volver al menú.")
    stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    selected_index = 0
    max_index = 4
    ultimo_pedido_seleccionado = -1  
    pedido_seleccionado_previously = False
    stdscr.clear()  
    stdscr.addstr("Revisando mesas...\n")
    stdscr.refresh() 
    mesas = get_request("/mesas")
    pedidos = get_request("/pedidos")

    while True:
        show_menu(stdscr, selected_index)
        option = stdscr.getch()

        if option == curses.KEY_UP:
            selected_index = max(selected_index - 1, 0)
        elif option == curses.KEY_DOWN:
            selected_index = min(selected_index + 1, max_index)
        elif option == ord('\n'):
            if selected_index == 0: 
                mesa_selected_index = 0
                show_mesas(stdscr, mesas, mesa_selected_index)
                while True:
                    mesa_option = stdscr.getch()
                    if mesa_option == curses.KEY_UP:
                        mesa_selected_index = max(mesa_selected_index - 1, 0)
                    elif mesa_option == curses.KEY_DOWN:
                        mesa_selected_index = min(mesa_selected_index + 1, len(mesas) - 1)
                    elif mesa_option == ord('q'):
                        break
                    show_mesas(stdscr, mesas, mesa_selected_index)
            elif selected_index == 1:
                stdscr.clear()
                pedido_selected_index = 0
                if pedidos:
                    while True:
                        stdscr.clear()
                        stdscr.addstr("Pedidos en preparación:\n")
                        for i, pedido in enumerate(pedidos):
                            mesa_correspondiente = next((mesa for mesa in mesas if str(mesa['_id']) == str(pedido['mesa'])), None)
                            capacidad_mesa = str(mesa_correspondiente['capacidad']) if mesa_correspondiente else 'Desconocida'
                            if i == pedido_selected_index:
                                stdscr.addstr(f"Pedido Mesa {capacidad_mesa}: {pedido['estado']}\n", curses.color_pair(1))
                            else:
                                stdscr.addstr(f"Pedido Mesa {capacidad_mesa}: {pedido['estado']}\n")
                        stdscr.addstr("\nUse las flechas para seleccionar un pedido y presione Enter para ver detalles. 'q' para volver.")
                        stdscr.refresh()

                        pedido_option = stdscr.getch()
                        if pedido_option == curses.KEY_UP:
                            pedido_selected_index = max(pedido_selected_index - 1, 0)
                        elif pedido_option == curses.KEY_DOWN:
                            pedido_selected_index = min(pedido_selected_index + 1, len(pedidos) - 1)
                        elif pedido_option == ord('\n'):
                            if pedido_selected_index == ultimo_pedido_seleccionado and pedido_seleccionado_previously:
                                pedido_seleccionado = pedidos[pedido_selected_index]
                                if pedido_seleccionado['estado'] != 'servido':
                                    resultado = post_request(f"/pedidos/{pedido_seleccionado['_id']['$oid']}/actualizar", {"estado": "servido"})
                                    stdscr.addstr("\nEstado del pedido actualizado a 'servido'.")
                                    stdscr.getch()
                                    pedidos = get_request("/pedidos")
                                pedido_seleccionado_previously = False
                            else:
                                pedido_seleccionado = pedidos[pedido_selected_index]
                                stdscr.clear()
                                stdscr.addstr(f"Detalles del pedido Mesa {capacidad_mesa}:\n")
                                for producto in pedido_seleccionado['productos']:
                                    nombre_producto = producto['item']['nombre']
                                    cantidad_producto = producto['cantidad']
                                    stdscr.addstr(f"- {nombre_producto} x{cantidad_producto}\n")
                                stdscr.getch()
                                ultimo_pedido_seleccionado = pedido_selected_index
                                pedido_seleccionado_previously = True
                        elif pedido_option == ord('q'):
                            break
            elif selected_index == 2: 
                if mesas:
                    mesas_ocupadas = [mesa for mesa in mesas if mesa['ocupada']]
                    if not mesas_ocupadas:
                        stdscr.clear()
                        stdscr.addstr("No hay mesas ocupadas.\nPresione cualquier tecla para volver.")
                        stdscr.getch()
                        continue 
                    mesa_selected_index = 0  
                    while True:
                        show_mesas(stdscr, mesas_ocupadas, mesa_selected_index, only_occupied=True)
                        mesa_option = stdscr.getch()
                        if mesa_option == curses.KEY_UP:
                            mesa_selected_index = max(mesa_selected_index - 1, 0)
                        elif mesa_option == curses.KEY_DOWN:
                            mesa_selected_index = min(mesa_selected_index + 1, len(mesas_ocupadas) - 1)
                        elif mesa_option == ord('\n'):
                            selected_mesa = mesas_ocupadas[mesa_selected_index]
                            resultado = post_request(f"/mesas/{selected_mesa['_id']}/vaciar", {})
                            stdscr.clear()
                            stdscr.addstr(f"Mesa {selected_mesa['capacidad']} vaciada.\n")
                            stdscr.addstr(f"{resultado['mensaje']}\n")
                            stdscr.getch()
                            stdscr.clear()
                            mesas = get_request("/mesas") 
                            break 
                        elif mesa_option == ord('q'):
                            break 
            elif selected_index == 3:
                stdscr.clear()
                if pedidos:
                    pedido_selected_index = 0
                    while True:
                        stdscr.clear()
                        stdscr.addstr("Seleccione un pedido para marcar como servido:\n")
                        for i, pedido in enumerate(pedidos):
                            mesa_correspondiente = next((mesa for mesa in mesas if str(mesa['_id']) == str(pedido['mesa'])), None)
                            capacidad_mesa = mesa_correspondiente['capacidad'] if mesa_correspondiente else 'Desconocida'
                            line_style = curses.color_pair(1) if i == pedido_selected_index else curses.A_NORMAL
                            stdscr.addstr(f"{i + 1}. Pedido de Mesa {capacidad_mesa} - Estado {pedido['estado']}\n", line_style)
                        stdscr.addstr("\nUse las flechas para seleccionar un pedido y presione Enter. 'q' para volver.")
                        stdscr.refresh()

                        pedido_option = stdscr.getch()
                        if pedido_option == curses.KEY_UP:
                            pedido_selected_index = max(pedido_selected_index - 1, 0)
                        elif pedido_option == curses.KEY_DOWN:
                            pedido_selected_index = min(pedido_selected_index + 1, len(pedidos) - 1)
                        elif pedido_option == ord('\n'):
                            pedido_seleccionado = pedidos[pedido_selected_index]
                            if pedido_seleccionado['estado'] != 'servido':
                                resultado = post_request(f"/pedidos/{pedido_seleccionado['_id']}/actualizar", {"estado": "servido"})
                                stdscr.clear()
                                stdscr.addstr(f"Estado del pedido actualizado a 'servido'.\n")
                                stdscr.getch()
                                pedidos = get_request("/pedidos")
                            else:
                                stdscr.clear()
                                stdscr.addstr("El pedido ya está marcado como 'servido'.\n")
                                stdscr.getch()
                            break 
                        elif pedido_option == ord('q'):
                            break 
                else:
                    stdscr.addstr("No hay pedidos disponibles para actualizar.\nPresione cualquier tecla para volver.")
                    stdscr.getch()

            elif selected_index == 4: 
                break
        elif option == ord('5'): 
            break

if __name__ == "__main__":
    curses.wrapper(main)

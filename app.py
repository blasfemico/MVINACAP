from registrar_usuario import registrar_usuario
from reconocimiento_facial import reconocimiento_facial

def menu():
    while True:
        print("\n--- Sistema de Seguridad Biométrica ---")
        print("1. Registrar nuevo usuario")
        print("2. Iniciar reconocimiento facial")
        print("3. Salir")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            nombre = input("Ingrese el nombre del usuario: ")
            registrar_usuario(nombre)
        elif opcion == "2":
            reconocimiento_facial()
        elif opcion == "3":
            print("Saliendo del sistema...")
            break
        else:
            print("Opción inválida, intente de nuevo.")

if __name__ == "__main__":
    menu()

import qiscord.listener
from qiscord.msg_handler.echo import Echo

def main():
    listener = qiscord.listener.Listenter(print_info=True)
    listener.start()

    echo_handler = Echo()
    echo_handler.enable = False

if __name__ == "__main__":
    main()
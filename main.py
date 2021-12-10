import qiscord.listener
from qiscord.msg_handler.echo import Echo
from sample_plugin.dicer import Dicer

def main():
    listener = qiscord.listener.Listenter(print_info=True)
    listener.start()

    echo_handler = Echo()
    echo_handler.enable = False

    dice_handler = Dicer()
    listener.add_handler(dice_handler)

if __name__ == "__main__":
    main()
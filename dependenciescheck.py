game_name = "Fantasy Strategia"

try:
    import thorpy
except ModuleNotFoundError:
    print("Could not load ThorPy ! ThorPy is needed to run "+game_name)
    print("Run 'pip install thorpy' in a console.")
    exit()


def exit_error(missing_module):
    text = "Could not load "+missing_module+". "+missing_module.capitalize()+\
            " is needed to run "+game_name+".\n\nTry running 'pip install "+\
            missing_module+"' in a console to install this dependency."
    print(text)
    import thorpy
    ap = thorpy.Application((800,600))
    thorpy.launch_blocking_alert("Missing module", text)
    ap.quit()
    exit()

try:
    import numpy
except ModuleNotFoundError:
    exit_error("numpy")
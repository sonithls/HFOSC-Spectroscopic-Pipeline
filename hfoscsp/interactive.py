# Author : Sonith L.S
# Contact : sonith.ls@iiap.res.in
__version__ = '0.0.7'

import inquirer


def options(message, choices):
    """
    Funnction for giving multiple options while running code.
    message : Message before giving different options.
    choices : List of chioses
    Ex : choices = ['Default', 'Manually']
    """
    question = [inquirer.List('x', message, choices)]
    answer = inquirer.prompt(question)
    print(answer["x"])
    answer = answer["x"]
    return answer


def multioptions(message, choices, default=''):
    """
    Funnction for giving multiple options while running code.
    message : Message before giving different options.
    choices : List of chioses
    Ex : choices = ['Default', 'Manually']
    """
    question = [inquirer.Checkbox('x', message, choices, default)]
    answer = inquirer.prompt(question)
    print(answer)
    answer = answer["x"]
    return answer

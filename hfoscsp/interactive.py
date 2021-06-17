"""Module provide interactive options."""

__author__ = 'Sonith L.S'
__contact__ = 'sonith.ls@iiap.res.in'
__version__ = '0.0.10'

import inquirer


def options(message, choices):
    """
    Provide multiple options while running code, but can select only one\
    option among them.

    Parameters
    ----------
        message : str
            Message before giving different options.
        choices : list
            List of choices
    Returns
    -------
        answer  : str
            Selected choice.
    Example
    -------
        choices = ['Default', 'Manually']
    """
    question = [inquirer.List('x', message, choices)]
    answer = inquirer.prompt(question)
    print(answer["x"])
    answer = answer["x"]
    return answer


def multioptions(message, choices, default=''):
    """
    Provide multiple options while running code, also can select multiple\
    option among them.

    Parameters
    ----------
        message : str
            Message before giving different options.
        choices : list
            List of choices
    Returns
    -------
        answer  : list
            List of selected choices.
    """
    question = [inquirer.Checkbox('x', message, choices, default)]
    answer = inquirer.prompt(question)
    print(answer)
    answer = answer["x"]
    return answer

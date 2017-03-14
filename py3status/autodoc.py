# -*- coding: utf-8 -*-

from py3status.docstrings import core_module_docstrings


def markdown_2_rst(lines):
    """
    Convert markdown to restructured text
    """
    out = []
    code = False
    for line in lines:
        # code blocks
        if line.strip() == '```':
            code = not code
            space = ' ' * (len(line.rstrip()) - 3)
            if code:
                out.append('\n\n%s.. code-block:: none\n\n' % space)
            else:
                out.append('\n')
        else:
            if code and line.strip():
                line = '    ' + line
            out.append(line)
    return out


def create_module_docs():
    """
    Create documentation for modules.
    """
    data = core_module_docstrings(format='rst')

    out = []
    # details
    for module in sorted(data.keys()):
        out.append(
            '\n{name}\n{underline}\n\n{details}\n'.format(
                name=module,
                underline='-' * len(module),
                details=''.join(markdown_2_rst(data[module])).strip()
            )
        )
    # write include file
    with open('../doc/modules-info.inc', 'w') as f:
        f.write(''.join(out))


def create_auto_documentation():
    """
    Create any include files needed for sphinx documentation
    """
    create_module_docs()


if __name__ == '__main__':
    create_auto_documentation()

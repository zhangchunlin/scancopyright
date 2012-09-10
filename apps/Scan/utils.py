#coding=utf-8

def get_path_css(path):
    cr = path.copyright
    cr_ih = path.copyright_inhouse
    cr_gpl = path.copyright_gpl
    cr_oos = path.copyright_oos
    if not(cr or cr_ih or cr_gpl or cr_oos):
        return 'no_cr'
    elif cr_ih and cr_gpl:
        return 'cr_conflict'
    elif cr_ih and cr_oos:
        return 'cr_mixed'
    elif cr_ih:
        return 'cr_ih'
    elif cr_gpl:
        return 'cr_gpl'
    elif cr_oos:
        return 'cr_oos'
    else:
        return 'cr'

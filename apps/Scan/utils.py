#coding=utf-8
import re
import cgi

def tagcopyright(text):
    def tagrepl(mobj):
        d = mobj.groupdict()
        if d['copyright']:
            tag = 'cr'
        elif d['inhouse']:
            tag = 'cr_ih'
        elif d['gpl']:
            tag = 'cr_gpl'
        elif d['oos']:
            tag = 'cr_oos'
        else:
            return mobj.group(0)
        #print tag,mobj.group(0)
        return "{{{%s}}}%s{{{/%s}}}"%(tag,mobj.group(0),tag)
    from uliweb import settings
    cobj = re.compile(settings.SCAN.RE_COPYRIGHT,re.M|re.I)
    text = cobj.sub(tagrepl,text)
    return text

re_string_html = re.compile(r'(?P<htmlchars>[<&>])|(?P<space>^[ \t]+)|(?P<lineend>\r\n|\r|\n)|(?P<protocal>(^|\s*)(http|ftp|https)://[\w\-\.,@?^=%&amp;:/~\+#]+)|(?P<tagcrbegin>\{\{\{)|(?P<tagcrend>\}\}\})', re.S|re.M|re.I)
re_string = re.compile(r'(?P<htmlchars>[<&>])|(?P<space>^[ \t]+)|(?P<lineend>\r\n|\r|\n)', re.S|re.M|re.I)
def text2html(text, tabstop=4, link=True):
    if not text:
        return ''
    def do_sub(m):
        c = m.groupdict()
        if c['htmlchars']:
            return cgi.escape(c['htmlchars'])
        if c['lineend']:
            return '<br/>'
        elif c['space']:
            t = m.group().replace('\t', '&nbsp;'*tabstop)
            t = t.replace(' ', '&nbsp;')
            return t
        elif c['tagcrbegin']:
            return '<'
        elif c['tagcrend']:
            return '>'
        else:
            url = m.group('protocal')
            if url.startswith(' '):
                prefix = ' '
                url = url[1:]
            else:
                prefix = ''
            return '%s<a href="%s">%s</a>' % (prefix, url, url)
    if link:
        return re.sub(re_string_html, do_sub, text)
    else:
        return re.sub(re_string, do_sub, text)

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

if __name__ == '__main__':
    text=("I like python!\r\n"
    "UliPad <<The Python Editor>>: http://code.google.com/p/ulipad/\r\n"
    "UliWeb <<simple web framework>>: http://uliwebproject.appspot.com\r\n"
    "My Blog: http://hi.baidu.com/limodou")
    print text2html(text)

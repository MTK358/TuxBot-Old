import re, urllib

def translate(from_lang, to_lang, text):
    params = urllib.urlencode({"BabelFishFrontPage": "yes",
                               "doit": "done",
                               "urltext": text,
                               "lp": from_lang + "_" + to_lang})
    try:
        response = urllib.urlopen("http://babelfish.yahoo.com/translate_txt", params)
    except IOError, e:
        return "(error: %s)" % (e)

    html = response.read()

    print html

    match = re.search(r'<div id="result">(<div [^>]*>)?(.*?)</div>', html)
    if match:
        return match.group(2)

    response.close()

    return "(error: could not extract translated text from response)"


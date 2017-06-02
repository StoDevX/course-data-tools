def parse_paragraph_as_list(string_with_br):
    paragraph = ' '.join(string_with_br.split())
    lines = [s.strip() for s in paragraph.split('<br>')]
    return [line
            for line in lines
            if line]

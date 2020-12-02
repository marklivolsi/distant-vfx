import yagmail


class EmailHandler:

    def __init__(self, gmail_username, gmail_password):
        self.client = yagmail.SMTP(gmail_username, gmail_password)

    def send(self, recipients, subject, contents):
        self.client.send(to=recipients, subject=subject, contents=contents)

    @staticmethod
    def format_html_table(rows):

        # Format the header row
        header_row = rows.pop(0)
        header_html = ''
        for col in header_row:
            header_html += '<th>{col}</th>'.format(col=col)

        html = '<table><thead><tr>{header_html}</tr></thead><tbody>'.format(header_html=header_html)

        # Format table rows
        row_html = ''
        for row in rows:
            row_html += '<tr>'
            for col in row:
                row_html += '<td>{col}</td>'.format(col=col)
            row_html += '</tr>'

        html += row_html + '</tbody></table>'
        return html

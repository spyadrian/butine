import pytest

from app.services.latex import latex_to_unicode


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Real author names from arXiv feeds.
        ("{\\O}ystein Gullbrekken", "Øystein Gullbrekken"),
        ("Sondre Kvalv{\\aa}g Schnell", "Sondre Kvalvåg Schnell"),
        ('B. T. G\\"ansicke', "B. T. Gänsicke"),
        ("J. -L. Gonz\\'alez-Carballo", "J. -L. González-Carballo"),
        ("E. Fern\\'andez-Ma\\~nanes", "E. Fernández-Mañanes"),
        ("Drago\\c{s}-Andrei \\c{S}erban", "Dragoş-Andrei Şerban"),  # \c is a cedilla
        ("R\\u{a}zvan-Alexandru Sm\\u{a}du", "Răzvan-Alexandru Smădu"),
        ("H\\^opital Piti\\'e Salp\\^etri\\`ere", "Hôpital Pitié Salpêtrière"),
        ('Nathana\\"el Lapidus', "Nathanaël Lapidus"),
        # Other accent forms.
        ("Mar{\\'\\i}a", "María"),
        ("Rodr\\'{\\i}guez", "Rodríguez"),
        ("{\\'E}mile", "Émile"),
        ("Ji\\v{r}\\'i \\v Cern\\'y", "Jiří Černý"),
        ("Pawe{\\l} Ko{\\l}odziej", "Paweł Kołodziej"),
        ("Stra\\ss e", "Straße"),
        ("Erd\\H{o}s", "Erdős"),
        ("J\\k{e}drzej", "Jędrzej"),
        ("Helgi Sigur{\\dh}sson", "Helgi Sigurðsson"),
        ("V. {\\DJ}uki\\'c", "V. Đukić"),
        ("Physics \\& Astronomy Department", "Physics & Astronomy Department"),
        ("University of S\\ ao Paulo", "University of Sao Paulo"),  # the feed lost the tilde
        # Names without LaTeX are left as they are.
        ("Xiaowei Wang", "Xiaowei Wang"),
        ("Øystein Gullbrekken", "Øystein Gullbrekken"),
        ("", ""),
    ],
)
def test_latex_to_unicode(raw, expected):
    assert latex_to_unicode(raw) == expected

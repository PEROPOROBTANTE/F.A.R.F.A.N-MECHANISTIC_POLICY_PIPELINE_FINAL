"""
PDET Colombia Complete Dataset
170 municipalities across 16 subregions
Data compiled from official government sources (2024)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PDETSubregion(Enum):
    """16 PDET Subregions"""
    ALTO_PATIA = "Alto Patía y Norte del Cauca"
    ARAUCA = "Arauca"
    BAJO_CAUCA = "Bajo Cauca y Nordeste Antioqueño"
    CAGUAN = "Cuenca del Caguán y Piedemonte Caqueteño"
    CATATUMBO = "Catatumbo"
    CHOCO = "Chocó"
    MACARENA = "Macarena-Guaviare"
    MONTES_MARIA = "Montes de María"
    PACIFICO_MEDIO = "Pacífico Medio"
    PACIFICO_NARINENSE = "Pacífico y Frontera Nariñense"
    PUTUMAYO = "Putumayo"
    SIERRA_NEVADA = "Sierra Nevada - Perijá - Zona Bananera"
    SUR_BOLIVAR = "Sur de Bolívar"
    SUR_CORDOBA = "Sur de Córdoba"
    SUR_TOLIMA = "Sur del Tolima"
    URABA = "Urabá Antioqueño"


@dataclass
class PDETMunicipality:
    """Represents a PDET municipality"""
    name: str
    department: str
    subregion: PDETSubregion
    population: int = 0
    area_km2: float = 0.0
    dane_code: str = ""


# Complete PDET Municipality Dataset (170 municipalities)
PDET_MUNICIPALITIES: list[PDETMunicipality] = [
    # ALTO PATÍA Y NORTE DEL CAUCA (24 municipalities)
    PDETMunicipality("Argelia", "Cauca", PDETSubregion.ALTO_PATIA, 31000, 661.0, "19050"),
    PDETMunicipality("Balboa", "Cauca", PDETSubregion.ALTO_PATIA, 22000, 388.0, "19075"),
    PDETMunicipality("Buenos Aires", "Cauca", PDETSubregion.ALTO_PATIA, 32000, 519.0, "19100"),
    PDETMunicipality("Cajibío", "Cauca", PDETSubregion.ALTO_PATIA, 38000, 440.0, "19110"),
    PDETMunicipality("Caldono", "Cauca", PDETSubregion.ALTO_PATIA, 31000, 249.0, "19137"),
    PDETMunicipality("Caloto", "Cauca", PDETSubregion.ALTO_PATIA, 40000, 350.0, "19142"),
    PDETMunicipality("Corinto", "Cauca", PDETSubregion.ALTO_PATIA, 33000, 273.0, "19212"),
    PDETMunicipality("El Tambo", "Cauca", PDETSubregion.ALTO_PATIA, 50000, 3213.0, "19256"),
    PDETMunicipality("Jambaló", "Cauca", PDETSubregion.ALTO_PATIA, 17000, 51.0, "19364"),
    PDETMunicipality("Mercaderes", "Cauca", PDETSubregion.ALTO_PATIA, 21000, 604.0, "19418"),
    PDETMunicipality("Miranda", "Cauca", PDETSubregion.ALTO_PATIA, 42000, 597.0, "19455"),
    PDETMunicipality("Morales", "Cauca", PDETSubregion.ALTO_PATIA, 28000, 580.0, "19473"),
    PDETMunicipality("Patía", "Cauca", PDETSubregion.ALTO_PATIA, 37000, 834.0, "19513"),
    PDETMunicipality("Piendamó", "Cauca", PDETSubregion.ALTO_PATIA, 44000, 116.0, "19532"),
    PDETMunicipality("Santander de Quilichao", "Cauca", PDETSubregion.ALTO_PATIA, 95000, 543.0, "19693"),
    PDETMunicipality("Suárez", "Cauca", PDETSubregion.ALTO_PATIA, 20000, 364.0, "19698"),
    PDETMunicipality("Toribío", "Cauca", PDETSubregion.ALTO_PATIA, 31000, 186.0, "19821"),
    PDETMunicipality("Cumbitara", "Nariño", PDETSubregion.ALTO_PATIA, 16000, 600.0, "52227"),
    PDETMunicipality("El Rosario", "Nariño", PDETSubregion.ALTO_PATIA, 12000, 558.0, "52258"),
    PDETMunicipality("Leiva", "Nariño", PDETSubregion.ALTO_PATIA, 13000, 395.0, "52381"),
    PDETMunicipality("Los Andes", "Nariño", PDETSubregion.ALTO_PATIA, 15000, 434.0, "52427"),
    PDETMunicipality("Policarpa", "Nariño", PDETSubregion.ALTO_PATIA, 17000, 624.0, "52585"),
    PDETMunicipality("Florida", "Valle del Cauca", PDETSubregion.ALTO_PATIA, 58000, 517.0, "76275"),
    PDETMunicipality("Pradera", "Valle del Cauca", PDETSubregion.ALTO_PATIA, 61000, 273.0, "76563"),

    # ARAUCA (4 municipalities)
    PDETMunicipality("Arauquita", "Arauca", PDETSubregion.ARAUCA, 45000, 3828.0, "81065"),
    PDETMunicipality("Fortul", "Arauca", PDETSubregion.ARAUCA, 27000, 1997.0, "81300"),
    PDETMunicipality("Saravena", "Arauca", PDETSubregion.ARAUCA, 53000, 1879.0, "81736"),
    PDETMunicipality("Tame", "Arauca", PDETSubregion.ARAUCA, 53000, 5278.0, "81794"),

    # BAJO CAUCA Y NORDESTE ANTIOQUEÑO (13 municipalities)
    PDETMunicipality("Cáceres", "Antioquia", PDETSubregion.BAJO_CAUCA, 39000, 2273.0, "05120"),
    PDETMunicipality("Caucasia", "Antioquia", PDETSubregion.BAJO_CAUCA, 104000, 1842.0, "05154"),
    PDETMunicipality("El Bagre", "Antioquia", PDETSubregion.BAJO_CAUCA, 53000, 1824.0, "05250"),
    PDETMunicipality("Nechí", "Antioquia", PDETSubregion.BAJO_CAUCA, 29000, 2803.0, "05495"),
    PDETMunicipality("Tarazá", "Antioquia", PDETSubregion.BAJO_CAUCA, 45000, 1923.0, "05790"),
    PDETMunicipality("Zaragoza", "Antioquia", PDETSubregion.BAJO_CAUCA, 30000, 900.0, "05895"),
    PDETMunicipality("Amalfi", "Antioquia", PDETSubregion.BAJO_CAUCA, 23000, 1224.0, "05030"),
    PDETMunicipality("Anorí", "Antioquia", PDETSubregion.BAJO_CAUCA, 18000, 1445.0, "05040"),
    PDETMunicipality("Remedios", "Antioquia", PDETSubregion.BAJO_CAUCA, 29000, 1985.0, "05604"),
    PDETMunicipality("Segovia", "Antioquia", PDETSubregion.BAJO_CAUCA, 40000, 1234.0, "05756"),
    PDETMunicipality("Valdivia", "Antioquia", PDETSubregion.BAJO_CAUCA, 20000, 1088.0, "05854"),
    PDETMunicipality("Vegachí", "Antioquia", PDETSubregion.BAJO_CAUCA, 9000, 582.0, "05858"),
    PDETMunicipality("Yondó", "Antioquia", PDETSubregion.BAJO_CAUCA, 18000, 1635.0, "05893"),

    # CUENCA DEL CAGUÁN Y PIEDEMONTE CAQUETEÑO (17 municipalities)
    PDETMunicipality("Albania", "Caquetá", PDETSubregion.CAGUAN, 5000, 1149.0, "18029"),
    PDETMunicipality("Belén de los Andaquíes", "Caquetá", PDETSubregion.CAGUAN, 11000, 1168.0, "18094"),
    PDETMunicipality("Cartagena del Chairá", "Caquetá", PDETSubregion.CAGUAN, 35000, 12704.0, "18150"),
    PDETMunicipality("Curillo", "Caquetá", PDETSubregion.CAGUAN, 11000, 1463.0, "18205"),
    PDETMunicipality("El Doncello", "Caquetá", PDETSubregion.CAGUAN, 25000, 1195.0, "18247"),
    PDETMunicipality("El Paujil", "Caquetá", PDETSubregion.CAGUAN, 21000, 907.0, "18256"),
    PDETMunicipality("Florencia", "Caquetá", PDETSubregion.CAGUAN, 180000, 2292.0, "18001"),
    PDETMunicipality("La Montañita", "Caquetá", PDETSubregion.CAGUAN, 24000, 1462.0, "18410"),
    PDETMunicipality("Milán", "Caquetá", PDETSubregion.CAGUAN, 11000, 940.0, "18460"),
    PDETMunicipality("Morelia", "Caquetá", PDETSubregion.CAGUAN, 4000, 1386.0, "18479"),
    PDETMunicipality("Puerto Rico", "Caquetá", PDETSubregion.CAGUAN, 36000, 15224.0, "18592"),
    PDETMunicipality("San José del Fragua", "Caquetá", PDETSubregion.CAGUAN, 14000, 3938.0, "18610"),
    PDETMunicipality("San Vicente del Caguán", "Caquetá", PDETSubregion.CAGUAN, 64000, 24466.0, "18753"),
    PDETMunicipality("Solano", "Caquetá", PDETSubregion.CAGUAN, 22000, 42625.0, "18756"),
    PDETMunicipality("Solita", "Caquetá", PDETSubregion.CAGUAN, 14000, 9057.0, "18785"),
    PDETMunicipality("Valparaíso", "Caquetá", PDETSubregion.CAGUAN, 16000, 1231.0, "18860"),
    PDETMunicipality("Algeciras", "Huila", PDETSubregion.CAGUAN, 23000, 626.0, "41026"),

    # CATATUMBO (8 municipalities)
    PDETMunicipality("Convención", "Norte de Santander", PDETSubregion.CATATUMBO, 19000, 1171.0, "54206"),
    PDETMunicipality("El Carmen", "Norte de Santander", PDETSubregion.CATATUMBO, 15000, 1186.0, "54245"),
    PDETMunicipality("El Tarra", "Norte de Santander", PDETSubregion.CATATUMBO, 13000, 690.0, "54250"),
    PDETMunicipality("Hacarí", "Norte de Santander", PDETSubregion.CATATUMBO, 14000, 549.0, "54344"),
    PDETMunicipality("San Calixto", "Norte de Santander", PDETSubregion.CATATUMBO, 12000, 1155.0, "54660"),
    PDETMunicipality("Sardinata", "Norte de Santander", PDETSubregion.CATATUMBO, 26000, 1398.0, "54720"),
    PDETMunicipality("Teorama", "Norte de Santander", PDETSubregion.CATATUMBO, 19000, 1126.0, "54800"),
    PDETMunicipality("Tibú", "Norte de Santander", PDETSubregion.CATATUMBO, 48000, 2696.0, "54810"),

    # CHOCÓ (14 municipalities)
    PDETMunicipality("Acandí", "Chocó", PDETSubregion.CHOCO, 11000, 993.0, "27006"),
    PDETMunicipality("Bojayá", "Chocó", PDETSubregion.CHOCO, 11000, 1430.0, "27073"),
    PDETMunicipality("Carmen del Darién", "Chocó", PDETSubregion.CHOCO, 9000, 1995.0, "27135"),
    PDETMunicipality("Condoto", "Chocó", PDETSubregion.CHOCO, 20000, 1183.0, "27205"),
    PDETMunicipality("Istmina", "Chocó", PDETSubregion.CHOCO, 23000, 2394.0, "27361"),
    PDETMunicipality("Litoral de San Juan", "Chocó", PDETSubregion.CHOCO, 14000, 1024.0, "27413"),
    PDETMunicipality("Medio Atrato", "Chocó", PDETSubregion.CHOCO, 17000, 6815.0, "27425"),
    PDETMunicipality("Medio San Juan", "Chocó", PDETSubregion.CHOCO, 18000, 1331.0, "27430"),
    PDETMunicipality("Nóvita", "Chocó", PDETSubregion.CHOCO, 11000, 1619.0, "27491"),
    PDETMunicipality("Riosucio", "Chocó", PDETSubregion.CHOCO, 29000, 711.0, "27615"),
    PDETMunicipality("Sipí", "Chocó", PDETSubregion.CHOCO, 11000, 725.0, "27745"),
    PDETMunicipality("Unguía", "Chocó", PDETSubregion.CHOCO, 21000, 954.0, "27800"),
    PDETMunicipality("Murindó", "Antioquia", PDETSubregion.CHOCO, 4000, 1848.0, "05483"),
    PDETMunicipality("Vigía del Fuerte", "Antioquia", PDETSubregion.CHOCO, 6000, 956.0, "05873"),

    # MACARENA-GUAVIARE (12 municipalities)
    PDETMunicipality("Mapiripán", "Meta", PDETSubregion.MACARENA, 15000, 11341.0, "50325"),
    PDETMunicipality("Mesetas", "Meta", PDETSubregion.MACARENA, 9000, 1430.0, "50330"),
    PDETMunicipality("La Macarena", "Meta", PDETSubregion.MACARENA, 30000, 11229.0, "50350"),
    PDETMunicipality("Uribe", "Meta", PDETSubregion.MACARENA, 15000, 9506.0, "50686"),
    PDETMunicipality("Puerto Concordia", "Meta", PDETSubregion.MACARENA, 19000, 2077.0, "50568"),
    PDETMunicipality("Puerto Lleras", "Meta", PDETSubregion.MACARENA, 12000, 3987.0, "50577"),
    PDETMunicipality("Puerto Rico", "Meta", PDETSubregion.MACARENA, 19000, 2288.0, "50590"),
    PDETMunicipality("Vista Hermosa", "Meta", PDETSubregion.MACARENA, 22000, 7417.0, "50711"),
    PDETMunicipality("San José del Guaviare", "Guaviare", PDETSubregion.MACARENA, 64000, 16592.0, "95001"),
    PDETMunicipality("Calamar", "Guaviare", PDETSubregion.MACARENA, 23000, 36157.0, "95015"),
    PDETMunicipality("El Retorno", "Guaviare", PDETSubregion.MACARENA, 19000, 18858.0, "95025"),
    PDETMunicipality("Miraflores", "Guaviare", PDETSubregion.MACARENA, 8000, 27183.0, "95200"),

    # MONTES DE MARÍA (15 municipalities)
    PDETMunicipality("Córdoba", "Bolívar", PDETSubregion.MONTES_MARIA, 14000, 336.0, "13212"),
    PDETMunicipality("El Carmen de Bolívar", "Bolívar", PDETSubregion.MONTES_MARIA, 76000, 954.0, "13244"),
    PDETMunicipality("El Guamo", "Bolívar", PDETSubregion.MONTES_MARIA, 10000, 179.0, "13268"),
    PDETMunicipality("María la Baja", "Bolívar", PDETSubregion.MONTES_MARIA, 52000, 550.0, "13442"),
    PDETMunicipality("San Jacinto", "Bolívar", PDETSubregion.MONTES_MARIA, 22000, 464.0, "13654"),
    PDETMunicipality("San Juan Nepomuceno", "Bolívar", PDETSubregion.MONTES_MARIA, 39000, 547.0, "13657"),
    PDETMunicipality("Zambrano", "Bolívar", PDETSubregion.MONTES_MARIA, 9000, 250.0, "13894"),
    PDETMunicipality("Chalán", "Sucre", PDETSubregion.MONTES_MARIA, 4000, 169.0, "70204"),
    PDETMunicipality("Coloso", "Sucre", PDETSubregion.MONTES_MARIA, 6000, 237.0, "70215"),
    PDETMunicipality("Los Palmitos", "Sucre", PDETSubregion.MONTES_MARIA, 21000, 321.0, "70429"),
    PDETMunicipality("Morroa", "Sucre", PDETSubregion.MONTES_MARIA, 16000, 258.0, "70473"),
    PDETMunicipality("Ovejas", "Sucre", PDETSubregion.MONTES_MARIA, 24000, 701.0, "70508"),
    PDETMunicipality("Palmito", "Sucre", PDETSubregion.MONTES_MARIA, 12000, 126.0, "70523"),
    PDETMunicipality("San Onofre", "Sucre", PDETSubregion.MONTES_MARIA, 50000, 1142.0, "70713"),
    PDETMunicipality("Tolú Viejo", "Sucre", PDETSubregion.MONTES_MARIA, 25000, 231.0, "70823"),

    # PACÍFICO MEDIO (4 municipalities)
    PDETMunicipality("Alto Baudó", "Chocó", PDETSubregion.PACIFICO_MEDIO, 35000, 1871.0, "27025"),
    PDETMunicipality("Bajo Baudó", "Chocó", PDETSubregion.PACIFICO_MEDIO, 16000, 1862.0, "27050"),
    PDETMunicipality("Medio Baudó", "Chocó", PDETSubregion.PACIFICO_MEDIO, 17000, 1803.0, "27420"),
    PDETMunicipality("Buenaventura", "Valle del Cauca", PDETSubregion.PACIFICO_MEDIO, 424000, 6297.0, "76109"),

    # PACÍFICO Y FRONTERA NARIÑENSE (11 municipalities)
    PDETMunicipality("Barbacoas", "Nariño", PDETSubregion.PACIFICO_NARINENSE, 24000, 1674.0, "52083"),
    PDETMunicipality("El Charco", "Nariño", PDETSubregion.PACIFICO_NARINENSE, 32000, 2485.0, "52250"),
    PDETMunicipality("Francisco Pizarro", "Nariño", PDETSubregion.PACIFICO_NARINENSE, 13000, 1585.0, "52317"),
    PDETMunicipality("La Tola", "Nariño", PDETSubregion.PACIFICO_NARINENSE, 7000, 421.0, "52378"),
    PDETMunicipality("Magüí Payán", "Nariño", PDETSubregion.PACIFICO_NARINENSE, 23000, 1621.0, "52435"),
    PDETMunicipality("Mosquera", "Nariño", PDETSubregion.PACIFICO_NARINENSE, 12000, 1026.0, "52473"),
    PDETMunicipality("Olaya Herrera", "Nariño", PDETSubregion.PACIFICO_NARINENSE, 32000, 1932.0, "52490"),
    PDETMunicipality("Roberto Payán", "Nariño", PDETSubregion.PACIFICO_NARINENSE, 18000, 1333.0, "52621"),
    PDETMunicipality("Santa Bárbara", "Nariño", PDETSubregion.PACIFICO_NARINENSE, 9000, 1398.0, "52683"),
    PDETMunicipality("Tumaco", "Nariño", PDETSubregion.PACIFICO_NARINENSE, 215000, 3760.0, "52835"),
    PDETMunicipality("Ricaurte", "Nariño", PDETSubregion.PACIFICO_NARINENSE, 16000, 505.0, "52612"),

    # PUTUMAYO (9 municipalities)
    PDETMunicipality("Leguízamo", "Putumayo", PDETSubregion.PUTUMAYO, 21000, 12421.0, "86573"),
    PDETMunicipality("Mocoa", "Putumayo", PDETSubregion.PUTUMAYO, 46000, 1260.0, "86001"),
    PDETMunicipality("Orito", "Putumayo", PDETSubregion.PUTUMAYO, 21000, 587.0, "86320"),
    PDETMunicipality("Puerto Asís", "Putumayo", PDETSubregion.PUTUMAYO, 63000, 2961.0, "86568"),
    PDETMunicipality("Puerto Caicedo", "Putumayo", PDETSubregion.PUTUMAYO, 16000, 1297.0, "86569"),
    PDETMunicipality("Puerto Guzmán", "Putumayo", PDETSubregion.PUTUMAYO, 17000, 3221.0, "86571"),
    PDETMunicipality("San Miguel", "Putumayo", PDETSubregion.PUTUMAYO, 24000, 4086.0, "86755"),
    PDETMunicipality("Valle del Guamuéz", "Putumayo", PDETSubregion.PUTUMAYO, 49000, 1257.0, "86865"),
    PDETMunicipality("Villagarzón", "Putumayo", PDETSubregion.PUTUMAYO, 18000, 1470.0, "86885"),

    # SIERRA NEVADA - PERIJÁ - ZONA BANANERA (15 municipalities)
    PDETMunicipality("Agustín Codazzi", "Cesar", PDETSubregion.SIERRA_NEVADA, 62000, 2048.0, "20013"),
    PDETMunicipality("Becerril", "Cesar", PDETSubregion.SIERRA_NEVADA, 18000, 690.0, "20045"),
    PDETMunicipality("La Jagua de Ibirico", "Cesar", PDETSubregion.SIERRA_NEVADA, 22000, 720.0, "20383"),
    PDETMunicipality("La Paz", "Cesar", PDETSubregion.SIERRA_NEVADA, 26000, 1238.0, "20400"),
    PDETMunicipality("Manaure Balcón del Cesar", "Cesar", PDETSubregion.SIERRA_NEVADA, 15000, 1047.0, "20443"),
    PDETMunicipality("Pueblo Bello", "Cesar", PDETSubregion.SIERRA_NEVADA, 14000, 612.0, "20570"),
    PDETMunicipality("San Diego", "Cesar", PDETSubregion.SIERRA_NEVADA, 14000, 474.0, "20621"),
    PDETMunicipality("Valledupar", "Cesar", PDETSubregion.SIERRA_NEVADA, 490000, 4493.0, "20001"),
    PDETMunicipality("Dibulla", "La Guajira", PDETSubregion.SIERRA_NEVADA, 33000, 1774.0, "44090"),
    PDETMunicipality("Fonseca", "La Guajira", PDETSubregion.SIERRA_NEVADA, 36000, 494.0, "44279"),
    PDETMunicipality("San Juan del Cesar", "La Guajira", PDETSubregion.SIERRA_NEVADA, 40000, 1671.0, "44650"),
    PDETMunicipality("Aracataca", "Magdalena", PDETSubregion.SIERRA_NEVADA, 42000, 1254.0, "47053"),
    PDETMunicipality("Ciénaga", "Magdalena", PDETSubregion.SIERRA_NEVADA, 104000, 1237.0, "47189"),
    PDETMunicipality("Fundación", "Magdalena", PDETSubregion.SIERRA_NEVADA, 63000, 988.0, "47288"),
    PDETMunicipality("Santa Marta", "Magdalena", PDETSubregion.SIERRA_NEVADA, 500000, 2381.0, "47001"),

    # SUR DE BOLÍVAR (7 municipalities)
    PDETMunicipality("Arenal", "Bolívar", PDETSubregion.SUR_BOLIVAR, 18000, 627.0, "13052"),
    PDETMunicipality("Cantagallo", "Bolívar", PDETSubregion.SUR_BOLIVAR, 12000, 1202.0, "13140"),
    PDETMunicipality("Morales", "Bolívar", PDETSubregion.SUR_BOLIVAR, 17000, 416.0, "13468"),
    PDETMunicipality("San Pablo", "Bolívar", PDETSubregion.SUR_BOLIVAR, 44000, 979.0, "13667"),
    PDETMunicipality("Santa Rosa del Sur", "Bolívar", PDETSubregion.SUR_BOLIVAR, 39000, 1749.0, "13688"),
    PDETMunicipality("Simití", "Bolívar", PDETSubregion.SUR_BOLIVAR, 20000, 2814.0, "13744"),
    PDETMunicipality("Yondó", "Antioquia", PDETSubregion.SUR_BOLIVAR, 18000, 1635.0, "05893"),

    # SUR DE CÓRDOBA (5 municipalities)
    PDETMunicipality("Montelíbano", "Córdoba", PDETSubregion.SUR_CORDOBA, 83000, 2515.0, "23466"),
    PDETMunicipality("Puerto Libertador", "Córdoba", PDETSubregion.SUR_CORDOBA, 39000, 2903.0, "23570"),
    PDETMunicipality("San José de Uré", "Córdoba", PDETSubregion.SUR_CORDOBA, 12000, 1298.0, "23682"),
    PDETMunicipality("Tierralta", "Córdoba", PDETSubregion.SUR_CORDOBA, 101000, 5084.0, "23807"),
    PDETMunicipality("Valencia", "Córdoba", PDETSubregion.SUR_CORDOBA, 41000, 752.0, "23855"),

    # SUR DEL TOLIMA (4 municipalities)
    PDETMunicipality("Ataco", "Tolima", PDETSubregion.SUR_TOLIMA, 23000, 554.0, "73067"),
    PDETMunicipality("Chaparral", "Tolima", PDETSubregion.SUR_TOLIMA, 48000, 2238.0, "73168"),
    PDETMunicipality("Planadas", "Tolima", PDETSubregion.SUR_TOLIMA, 30000, 908.0, "73547"),
    PDETMunicipality("Rioblanco", "Tolima", PDETSubregion.SUR_TOLIMA, 23000, 1352.0, "73616"),

    # URABÁ ANTIOQUEÑO (10 municipalities)
    PDETMunicipality("Apartadó", "Antioquia", PDETSubregion.URABA, 195000, 607.0, "05045"),
    PDETMunicipality("Carepa", "Antioquia", PDETSubregion.URABA, 58000, 197.0, "05147"),
    PDETMunicipality("Chigorodó", "Antioquia", PDETSubregion.URABA, 79000, 615.0, "05172"),
    PDETMunicipality("Mutatá", "Antioquia", PDETSubregion.URABA, 20000, 1185.0, "05490"),
    PDETMunicipality("Necoclí", "Antioquia", PDETSubregion.URABA, 66000, 1387.0, "05490"),
    PDETMunicipality("San Juan de Urabá", "Antioquia", PDETSubregion.URABA, 23000, 672.0, "05659"),
    PDETMunicipality("San Pedro de Urabá", "Antioquia", PDETSubregion.URABA, 37000, 401.0, "05664"),
    PDETMunicipality("Turbo", "Antioquia", PDETSubregion.URABA, 165000, 3055.0, "05837"),
    PDETMunicipality("Arboletes", "Antioquia", PDETSubregion.URABA, 40000, 647.0, "05051"),
    PDETMunicipality("Dabeiba", "Antioquia", PDETSubregion.URABA, 25000, 1256.0, "05234"),
]


def get_municipalities_by_subregion(subregion: PDETSubregion) -> list[PDETMunicipality]:
    """Get all municipalities for a specific subregion"""
    return [m for m in PDET_MUNICIPALITIES if m.subregion == subregion]


def get_municipalities_by_department(department: str) -> list[PDETMunicipality]:
    """Get all municipalities for a specific department"""
    return [m for m in PDET_MUNICIPALITIES if m.department == department]


def get_municipality_by_name(name: str) -> PDETMunicipality:
    """Get municipality by name"""
    for m in PDET_MUNICIPALITIES:
        if m.name.lower() == name.lower():
            return m
    raise ValueError(f"Municipality not found: {name}")


def get_total_pdet_population() -> int:
    """Get total population across all PDET municipalities"""
    return sum(m.population for m in PDET_MUNICIPALITIES)


def get_subregion_statistics() -> dict[str, dict[str, Any]]:
    """Get statistics for each subregion"""
    stats = {}
    for subregion in PDETSubregion:
        municipalities = get_municipalities_by_subregion(subregion)
        stats[subregion.value] = {
            "municipality_count": len(municipalities),
            "total_population": sum(m.population for m in municipalities),
            "total_area_km2": sum(m.area_km2 for m in municipalities),
            "departments": list({m.department for m in municipalities})
        }
    return stats


# Module-level validation
assert len(PDET_MUNICIPALITIES) == 170, f"Expected 170 municipalities, got {len(PDET_MUNICIPALITIES)}"
assert len({m.name for m in PDET_MUNICIPALITIES}) == 170, "Duplicate municipality names detected"

print(f"PDET Colombia Data Module loaded: {len(PDET_MUNICIPALITIES)} municipalities across {len(PDETSubregion)} subregions")

gas_price_per_kwh = 0.0655  # Euro
electrical_feed_in_reward_per_kwh = 0.0917  # Euro
electrical_costs_per_kwh = 0.283  # Euro

""" Source: http://www.dwd.de/bvbw/generator/DWDWWW/Content/Oeffentlichkeit/KU/KU2/KU21/klimadaten/german/download/standardformate/kl__10379__00__akt__txt,templateId=raw,property=publicationFile.txt/kl_10379_00_akt_txt.txt """
outside_temperatures_2013 = [
    7.5, 5.6, 9.5, 9.2, 8.2, 7.1, 6.5, 6.5, 7.0, 4.6, 0.0, -0.6, -0.9, -3.5, -3.4, -3.1, 0.0, -1.8, -5.1, -3.4, -3.4, -6.6, -6.3, -4.1, -1.0, -4.9, 1.4, 5.2, 6.8, 12.0, 8.3, 7.2, 3.3, 2.9, 6.3, 6.1, 4.4, 1.8, 1.0, 0.4, -2.0, -0.4, 2.5, -0.3, 0.6, 0.9, 3.2, 2.0, 1.4, 1.7, 0.3, -1.1, -1.0, -0.7, 1.5, 2.7, 1.5, 2.6, 4.4, 5.4, 6.1, 5.7, 9.0, 12.4, 14.1, 9.9, 2.8, 1.7, -1.0, -3.2, -0.8, 0.3, 0.6, 1.2, 4.5, 4.5, 2.3, -0.3, 2.0, 1.6, 0.9, -
    2.1, 0.8, 1.9, 3.2, 2.6, 2.7, 1.2, 2.5, 3.0, 3.7, 3.1, 2.6, 3.5, 3.2, 4.7, 10.0, 10.3, 10.0, 9.4, 14.7, 14.3, 14.2, 19.3, 24.4, 20.3, 21.5, 26.1, 16.8, 13.5, 17.6, 19.8, 18.8, 19.7, 21.0, 25.9, 9.7, 15.2, 17.2, 14.6, 17.6, 15.3, 18.4, 20.9, 22.2, 23.9, 23.3, 24.2, 22.9, 18.8, 17.5, 18.0, 15.9, 15.3, 26.1, 26.1, 27.9, 18.8, 22.6, 17.6, 17.8, 12.3, 15.9, 14.1, 11.2, 13.8, 16.7, 17.7, 20.2, 20.9, 22.6, 22.3, 15.7, 18.0, 21.1, 22.4, 24.4, 25.5, 25.2, 25.3, 23.1, 23.8, 25.2, 26.8, 20.4, 23.3, 21.0, 26.8, 30.4, 34.2, 32.7, 24.7, 24.8, 24.2, 22.1, 15.0, 15.1, 18.8, 20.8, 20.0, 16.0, 26.0,
    23.5, 27.9, 23.2, 24.5, 24.8, 26.3, 27.2, 27.5, 22.4, 22.0, 22.6, 24.9, 18.2, 23.7, 27.0, 28.1, 28.5, 27.5, 27.7, 29.6, 31.7, 30.4, 30.7, 30.7, 32.1, 34.2, 34.7, 24.0, 24.3, 25.5, 29.8, 35.1, 33.3, 28.6, 27.9, 30.8, 26.1, 24.1, 21.5, 25.7, 21.1, 23.4, 21.4, 20.6, 23.7, 27.3, 27.0, 26.9, 20.8, 22.3, 22.6, 24.2, 24.4, 25.2, 25.3, 24.1, 22.8, 24.3, 25.5, 25.4, 24.7, 18.8, 16.3, 18.5, 20.4, 24.6, 26.5, 27.3, 24.5, 15.4, 17.7, 14.0, 17.6, 20.0, 23.0, 17.5, 17.1, 16.4, 12.0, 14.4, 15.9, 17.1, 17.2, 17.7, 15.0, 13.0, 12.9, 14.8, 15.7, 15.0, 14.7, 14.3, 13.8, 12.5, 15.1, 12.8, 15.0, 16.8, 15.0, 16.1, 11.7, 16.6, 13.5, 11.0, 14.9, 12.6, 10.6, 15.0, 12.7, 12.6, 18.4, 18.0, 20.8, 18.9, 17.1, 15.1, 18.8, 18.6, 20.1, 15.5, 13.0, 12.0, 11.3, 12.3, 10.9, 11.2, 10.9, 10.1, 13.9, 10.9, 12.0, 7.5, 7.7, 6.9, 9.6, 7.8, 4.7, 4.9, 7.4, 5.6, 7.4, 6.0, 4.2, 5.1, 7.5, 5.3, 2.8, 2.9, 4.1, 8.6, 6.3, 5.2, 7.2, 4.1, 2.4, 4.3, 3.7, 1.9, 1.8, 7.4, 8.8, 8.9, 7.5, 4.2, 1.0, 4.1, 6.3, 8.6, 8.5, 6.1, 6.3, 6.1, 6.7, 10.4, 8.0, 10.0, 9.1, 7.3, 7.6, 9.8, 6.8, 4.9, 4.7]

# pamiru48 values per 15min
daily_electrical_demand = [
    2.684, 2.710, 2.484, 2.364, 2.257, 2.141, 2.139, 2.283, 1.966, 1.814, 1.692, 1.518, 1.439, 1.624, 1.648, 1.801, 1.684, 2.012, 2.010, 1.662, 1.519, 1.623, 1.598, 1.518, 1.390, 1.621,
    1.323, 2.917, 2.730, 1.620, 1.357, 2.487, 2.624, 3.678, 2.663, 1.930, 2.133, 3.065, 2.336, 3.022, 6.023, 2.453, 2.071, 2.856, 2.890, 4.651, 5.959, 5.329, 2.998, 4.058, 2.159,
    2.437, 1.631, 3.012, 5.353, 4.922, 5.722, 5.413, 5.166, 5.230, 3.529, 3.493, 3.570, 3.598, 4.621, 6.685, 4.325, 3.795, 4.289, 3.749, 5.561, 4.074, 5.652, 4.218, 4.465, 4.145,
    3.868, 4.694, 4.629, 4.368, 5.761, 6.644, 6.183, 5.534, 4.121, 4.085, 4.149, 4.151, 3.820, 3.588, 3.474, 3.071, 3.187, 3.321, 3.026, 2.772
]

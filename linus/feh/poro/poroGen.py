## Refresher: −8 LV 1 stat total, ±0% or −5% growth
## "Advanced": +10% growth
## "Trainee": −8 LV 1 stat total, +30% growth
## "Veteran": +8 LV 1 stat total, -30% growth

unitGenerations = {}
unitGenerations["Infantry"] = {}
unitGenerations["Armored"] = {}
unitGenerations["Cavalry"] = {}
unitGenerations["Flying"] = {}

unitGenerations["Infantry"]["Melee"] = [
    (47, 255),
    (48, 265),
    (49, 275),
    (51, 280),
    (53, 285),
    (54, 295),
    (55, 305),
]

unitGenerations["Infantry"]["RangedPhys"] = [
    (44, 240),
    (45, 245),
    (47, 265),
    (48, 275),
    (50, 280),
    (51, 290),
]

unitGenerations["Infantry"]["RangedMag"] = [
    (44, 240),
    (45, 245),
    (46, 255),
    (47, 265),
    (49, 270),
    (50, 280),
]

unitGenerations["Armored"]["Melee"] = [
    (54, 265),
    (55, 275),
    (56, 285),
    (57, 295),
    (58, 305),
]

unitGenerations["Armored"]["RangedPhys"] = [
    (52, 260),
    (53, 270),
    (53, 280),
    (54, 290),
    (55, 300),
]

unitGenerations["Armored"]["RangedMag"] = [(52, 260), (52, 270), (53, 280), (54, 290)]

unitGenerations["Cavalry"]["Melee"] = [
    (46, 250),
    (46, 255),
    (47, 265),
    (49, 275),
    (50, 285),
    (51, 295),
]

unitGenerations["Cavalry"]["RangedPhys"] = [
    (43, 235),
    (44, 245),
    (44, 260),
    (46, 270),
    (47, 280),
]

unitGenerations["Cavalry"]["RangedMag"] = [(43, 235), (43, 250), (45, 260), (46, 270)]

unitGenerations["Flying"]["Melee"] = [
    (47, 255),
    (47, 265),
    (50, 270),
    (51, 280),
    (52, 290),
]

unitGenerations["Flying"]["RangedPhys"] = [
    (44, 245),
    (45, 255),
    (46, 265),
    (48, 275),
    (49, 285),
]

unitGenerations["Flying"]["RangedMag"] = [
    (44, 240),
    (44, 245),
    (45, 255),
    (47, 265),
    (48, 275),
    (49, 285),
]

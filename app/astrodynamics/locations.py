from orbit_predictor.locations import Location as LocationBase


class Location(LocationBase):

    def __repr__(self):
        s = '<Location '
        if self.name:
            s += self.name + ' '
        s += f'({self.latitude_deg:.4f}, {self.longitude_deg:.4f})'
        s += '>'
        return s

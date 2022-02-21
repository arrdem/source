module shelving_leg(height) {
    linear_extrude(height)
    polygon([
        [0, 0],
        [1, 0],
        [1, 0.125],
        [0.125, 0.125],
        [0.125, 1],
        [0, 1],
    ]);
}

module shelving_legs(width, depth, height) {
    union() {
        translate([0, 0, 0])
        rotate([0, 0, 0])
        shelving_leg(height);

        translate([width, 0, 0])
        rotate([0, 0, 90])
        shelving_leg(height);

        translate([0, depth, 0])
        rotate([0, 0, -90])
        shelving_leg(height);

        translate([width, depth, 0])
        rotate([0, 0, 180])
        shelving_leg(height);
    }
}

module shelving_shelves(width, depth, height, shelves) {
    for (i = [0:((height-2)/(shelves - 1)):height-2]) {
        translate([0, 0, i])
        cube([width, depth, 2]);
    }
}

module shelving(width, depth, height, shelves=4) {
    shelving_legs(width, depth, height);
    shelving_shelves(width, depth, height, shelves);
}

shelving(48, 24, 78);
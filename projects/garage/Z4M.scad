module scale_uniform(f) {
    scale([f, f, f])
        children();
}

module z4m() {
    // reference dimensions
    // cube([73, 171, 51]);

    scale_uniform(1.36)
    translate([43, 63, 1.4])
    rotate([0.4, 0, 180])
    import("BMW Z4M.stl");
}

z4m();
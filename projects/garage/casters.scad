function caster_axel(wheel_r, axel_r) = [1 + axel_r, wheel_r + axel_r, 0];

module caster_bracket(wheel_r, wheel_h, axel_r, plate_t, padding=0.125, $fn=$fn) {
    plate_side = wheel_r + axel_r + 1;
    
    module caster_plate(
        wheel_r,
        axel_r,
        plate_t,
    ) {
        difference() {
            linear_extrude(plate_t)
            polygon([
                [0, 0],
                [0, plate_side],
                [2 + axel_r * 2, plate_side],
                [plate_side, 2 + axel_r * 2],
                [plate_side, 0],
            ]);
            
            axel = caster_axel(wheel_r, axel_r);
            translate(axel)
            cylinder(r=axel_r, h=plate_t, $fn=$fn);
        }
    }

    translate([0, -plate_t, 0])
    union() {
        translate([0, plate_t, 0]);
        caster_plate(wheel_r, axel_r, plate_t);

        translate([0, plate_t, wheel_h + (plate_t + padding * 2)])
        caster_plate(wheel_r, axel_r, plate_t);
        
        cube([plate_side, plate_t, wheel_h + ((plate_t + padding) * 2)]);
    }
}

module caster(
    wheel_r,
    wheel_h,
    axel_r,
    axel_h,
    bearing_r=0,
    bearing_h=0,
    plate_t=0.125,
    padding=0.125,
    $fn=$fn,
) {
    rotate([-90, 0, -90])
    translate([-(caster_axel(wheel_r, axel_r).y), bearing_h - (wheel_r * 2) - 1 + plate_t + padding, -((wheel_h/2) + plate_t + padding)])
    union() {
        caster_bracket(wheel_r, wheel_h, axel_r, plate_t, padding, $fn=$fn);
        
        translate(caster_axel(wheel_r, axel_r)) {
            translate([0, 0, plate_t + padding])
            cylinder(r = wheel_r, h=wheel_h, $fn=$fn);
            
            translate([0, 0, -padding]) {
                cylinder(r = axel_r, h = (wheel_h + (2* plate_t) + (padding*4)), $fn=$fn);
            }
        }
        
        translate([caster_axel(wheel_r, axel_r).y, 0, (wheel_h/2) + plate_t + padding])
        rotate([90, 0, 0]) {
            cylinder(r = bearing_r, h=bearing_h);
            
            translate([0, 0, bearing_h])
            cylinder(r=axel_r, h=axel_h, $fn=$fn);
        }
    }
}

caster(
    // wheel (r, h)
    5, 1, 
    // axel (r, h)
    0.5, 1,
    // bearing (r, h)
    0.75, 0.25,
    $fn=16
);
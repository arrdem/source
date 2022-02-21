use <steel-shelving.scad>
use <Z4M.scad>
use <tire-loft.scad>
use <printer-rack.scad>

// Note 16" stud spacing
// Note 2.5" downgrade over run of garage; height to minimums

module pass() {
}

module do() {
    children();
}

module garage_perimeter() {
    union() {
        polygon([
            [0, 0],
            [0, 232],
            [40, 232],
            [40, 238],
            [-6, 238],
            [-6, -6],
            [5, -6],
            [5, 0],
            [0, 0],
        ]);

        polygon([
            [201, 0],
            [196, 0],
            [196, -6],
            [207, -6],
            [207, 198],
            [207 - 72, 198],
            [207 - 72, 238],
            [207 - 72 - 62, 238],
            [207 - 72 - 62, 232],
            [207 - 72 - 6, 232],    
            [207 - 72 - 6, 192],    
            [201, 192],    
        ]);
    }
}

// walls
union() {
    // FIXME: Draw the walls downgrade
    linear_extrude(height=96)
    garage_perimeter();
    
    // FIXME: Draw the floor

    // Garage door frame
    translate([0, -6, 90])
    cube([201, 6, 6]);
    
    // Pedestrian door frame
    translate([0, 232, 84])
    cube([129, 6, 12]);
}

module label(text="label",
             textsize=4,
             pos=[0,0,0],
             dpos=[10,0,10],
             linesize=0.2,
             length=20,
             anglexyz=[0,45,90])
{
    p1 = pos + dpos;
    if ($preview) 
        color("black") {
            line(pos, p1, linesize);
            translate(p1)
                rotate($vpr)
                        text(text, size = textsize);
    }
}

module line(p1=[0,0,0], p2=[0,0,10], r=.1) {
    hull() {
        translate(p1) sphere(r);
        translate(p2) sphere(r);
    }
}

// car (rough, assuming driver side door open)
translate([45 + 24 + 18, 10, 0])
color("blue")
z4m();

// south side workspace

//// power pulls
translate([0, 0, 44]) {
    let(outlets=4) {
        translate([1, 232, 2])
        rotate([90, 0, 0])
        cylinder(r=0.5, h=16 + 48 * (outlets - 1));
        
        for(i=[0:outlets-1]) {
            translate([0, 232 - 4 - 16 - i*48, 0])
            cube([3, 4, 4]);
        }
    }
}

//// printer rack
translate([4, 232 - 37, 0]) {
    pass()
    do() {
        cube([42, 24, 92]);
        label("servers", pos=[21, 12, 92]);
    }
    do() {
        translate([33, 0, 0])
        rotate([0, 0, 90])
        printer_rack();
        label("printers", pos=[19, 21, 80]);
    }
}

toolchest_size=44;

//// tool chest
translate([4, 232 - 37 - 1 - toolchest_size, 0]) {
    do() {
        color("red")
        cube([18.6, toolchest_size, 42.5]);
    
        label("Tool chest", pos=[9.3, 25, 45.2]);
    }
}

//// worktop
let(tops=2)
translate([24 + 1, 232 - 1 - 37 - 1 - toolchest_size - 1- (48 * tops), 0]) {
    rotate([0, 0, 90])
    shelving(48 * tops, 24, 32, shelves=3);
    label("Worktop", pos=[-12, (48*tops)/2, 32]);
}

//// bike hanger
pass()
cube([50, 33, 60]);

// north side storage
translate([201 - 24 - 1, 1, 0]) {
    for (i=[0:2]) {
        translate([0, (48 + 1) * i, 0]) {
            color("red")
            shelving(24, 48, 78);
            label("Deep storage", pos=[12, 24, 90]);
        }
    }
}

// Current tire rack
translate([201, 148, 65]) {
    rotate([0, 0, 90])
    tire_loft();
    label("Tire storage", pos=[-14.5, 22, 30]);
}

translate([201, 148, 32])
rotate([0, 0, 90])
tire_loft();

// sherpa
translate([201 - 13, 192, 0])
rotate([0, 0, 270])
cube([42, 12, 25]);

// trash can
translate([90, 232-14, 0]) {
    let (height=28, wall=0.25)
    difference() {
        cylinder(h=height, d=23);
        translate([0, 0, wall])
        cylinder(h=height, d=23 - (wall * 2));
    }
}

// IT gear
translate([129-19, 232-32, 0]) {
    translate([0, 0, 84])
    cube([19, 24, 15]);
    
    cube([24, 24, 32]);
}

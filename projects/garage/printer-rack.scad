use <box.scad>
use <casters.scad>

function mm2in(x) = x * 0.0393701;

mdf_thickness = 0.75;
padding = mdf_thickness;
pin_inset = 3;

function padded(dims, padding) = [for(e=dims) e+padding];

// dimensions for things
prusa = padded([mm2in(180 * 2 + 504), mm2in(115 + 660), mm2in(910)], padding);
cr10 = padded([19, 27, 25], padding);
repbox = padded([19, 12.5, 12.5], padding);
cart = [prusa.x, prusa.y, 6.75 + mdf_thickness];

module cart() {
    for(x=[pin_inset, cart.x - pin_inset])
    for(y=[pin_inset, cart.y - pin_inset])
    translate([x, y, 0])
    caster(
        // wheel (r, h)
        3, 1, 
        // axel (r, h)
        0.5, 1,
        // bearing (r, h)
        0.75, 0.25,
        $fn=16
    );
    
    translate([0, 0, cart.z - mdf_thickness])
    ccube([prusa.x + (mdf_thickness * 2), prusa.y + (mdf_thickness * 2), mdf_thickness]);
}

module printer_rack() {
    translate([0, 0, 0])
    cart();
       
    translate([0, 0, cart.z])
    box(prusa, mdf_thickness);

    translate([0, 0, cart.z + prusa.z])
    box([prusa.x, prusa.y, repbox.z], mdf_thickness);

    translate([0, 0, cart.z + prusa.z + repbox.z + mdf_thickness * 2])
    box([prusa.x, prusa.y, cr10.z], mdf_thickness);
}

printer_rack();
echo(prusa);
var barcode = "";
var scanned_barcode = "";
var barcodeTimer;
var interfaceTimer;
var account = {};
var funds = "";
var secretkey = "";
var mode = "scanning"
var current = document.querySelector(".current");
var icon = document.querySelector(".icon");
var lasttapstate = false;

function checkTapState() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/api/tapstate", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (this.readyState != 4) {
            return;
        }
        setTimeout(checkTapState, 250);
        if (this.status == 200) {
            var data = JSON.parse(this.responseText);
            var active = false;
            data.forEach(tap => {
                if (tap.state === 1) {
                    active = true;
                }
            });
            if (active & !lasttapstate) {
                lasttapstate = true;
                if (mode === "prepour") {
                    mode = "pouring";
                    refreshInterface();
                } else if (mode === "pouring") {

                } else {
                    mode = "alarm";
                    refreshInterface();
                    var report = new XMLHttpRequest();
                    report.open("POST", "/api/report", true);
                    report.setRequestHeader("Content-Type", "application/json");
                    report.send();
                }
            } else if (!active & lasttapstate) {
                lasttapstate = false;
                if (mode === "alarm") {
                    mode = "scanning";
                    if (interfaceTimer) {
                        clearTimeout(interfaceTimer);
                    }
                    interfaceTimer = setTimeout(resetMode, 2000);
                } else if (mode === "pouring") {
                    lookupAttendee(scanned_barcode);
                }
            }
        } else {
            M.toast({displayLength: 10000, html: "Failed to request tapstate: Server returned "+this.status});
        }
    }
    xhr.send();
}

setTimeout(checkTapState, 250);

function clearBarcode() {
    console.log("Clearing barcode");
    barcode = "";
}

function pourDrink() {
    if (mode === "status") {
        console.log("Pouring Drink for: " + account.name);
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/api/pour", true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) {
                return;
            }
            if (this.status == 200) {
                var data = JSON.parse(this.responseText);
                if (data.success) {
                    console.log("Poured Drink Successfully!");
                    mode = "prepour";
                    refreshInterface();
                } else {
                    mode = "failed";
                    refreshInterface();
                    M.toast({displayLength: 10000, html: data.error});
                }
            }
            else {
                M.toast({displayLength: 10000, html: "Failed to request pour: Server returned "+this.status});
                mode = "failed";
                refreshInterface();
            }
        }
        xhr.send(JSON.stringify({account: account.id, amount: -200, note: "Poured a Coldbrew", "secret": secretkey}));
        mode = "loading";
        refreshInterface();
    }
}

function resetMode() {
    if (mode === "pouring") {
        mode = "status";
    } else if (mode === "poured") {
        lookupAttendee(scanned_barcode);
        return;
    } else {
        account = {};
        funds = "";
        mode = "scanning";
    }
    refreshInterface();
}

function refreshInterface() {
    if (mode === "scanning") {
        clearTimeout(interfaceTimer);
        current.innerHTML = "<h4>Please scan your badge...</h4>";
        document.body.style.backgroundColor = "black";
        icon.style.color = "grey";
    } else if (mode === "unknown") {
        clearTimeout(interfaceTimer);
        current.innerHTML = "<div><div class='register'><h4>You Need To Register</h4></div><div class='register'><h4>https://coldbrew.magevent.net/</h4></div></div>";
        interfaceTimer = setTimeout(resetMode, 5000);
    } else if (mode === "status") {
        current.innerHTML = "<div><div class='name'>"+account.name+"</div><div class='funds'>"+funds+"</div><div><i onclick='resetMode()' class='left large material-icons'>clear</i><i onclick='pourDrink()' class='right large material-icons'>send</i></div></div>";
        icon.style.color = "white";
        if (interfaceTimer) {
            clearTimeout(interfaceTimer);
        }
        interfaceTimer = setTimeout(resetMode, 20000);
    } else if (mode === "pouring") {
        current.innerHTML = "<h3>Pouring!</h3>";
        icon.style.color = "green";
        mode = "poured"
        if (interfaceTimer) {
            clearTimeout(interfaceTimer);
        }
        interfaceTimer = setTimeout(resetMode, 5000);
    } else if (mode === "alarm") {
        current.innerHTML = "<h3>UNPAID DRINK!</h3>";
        icon.style.color = "yellow";
        document.body.style.backgroundColor = "red";
        if (interfaceTimer) {
            clearTimeout(interfaceTimer);
        }
        interfaceTimer = setTimeout(resetMode, 15000);
    } else if (mode === "prepour") {
        current.innerHTML = "<h3>You May Pour A Drink!</h3>";
        icon.style.color = "green";
        if (interfaceTimer) {
            clearTimeout(interfaceTimer);
        }
        interfaceTimer = setTimeout(resetMode, 15000);
    } else if (mode === "loading") {
        current.innerHTML = "<h3>Please Wait...</h3>";
        if (interfaceTimer) {
            clearTimeout(interfaceTimer);
        }
    } else if (mode === "failed") {
        current.innerHTML = "<h3>No ColdBrew For You!</h3>";
        icon.style.color = "red";
        if (interfaceTimer) {
            clearTimeout(interfaceTimer);
        }
        interfaceTimer = setTimeout(resetMode, 5000);
    } else if (mode === "secret") {
        current.innerHTML = '<div><h3>You Must Authorize This Terminal</h3><br><input id="hex" type="text"></div>';
        $('#hex').keyboard({
            layout: 'custom',
            customLayout: {
                'normal' : [
                    'C D E F',
                    '8 9 A B',
                    '4 5 6 7',
                    '0 1 2 3',
                    '{bksp} {a} {c}'
                ]
            },
            maxLength: 8,
            appendLocally: true,
            reposition: true,
            restrictInput: true,
            restrictInclude : 'a b c d e f',
            useCombos: true,
            acceptValid: true,
            validate: function(keyboard, value, isClosing) {
                return value.length == 8;
            }
        });
        $('#hex').bind('accepted', function(e, keyboard, el) {
            Cookies.set("secretkey", el.value);
            secretkey = el.value;
            mode = "scanning";
            refreshInterface();
        });
    }
}

function lookupAttendee() {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/accounts/lookup", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (this.readyState != 4) {
            return;
        }
        if (this.status == 200) {
            var data = JSON.parse(this.responseText);
            if (data.success) {
                account = data.account;
                funds = data.funds;
                mode = "status";
                refreshInterface();
            } else {
                if (data.type === "invalid") {
                    M.toast({displayLength: 10000, html: "Failed to lookup account: " + data.error});
                } else {
                    mode = "unknown";
                    refreshInterface();
                }
            }
        }
        else {
            M.toast({displayLength: 10000, html: "Failed to lookup account: Server returned "+this.status});
        }
    }
    xhr.send(JSON.stringify({barcode: scanned_barcode}));
}

function handleBarcode(evt) {
    if (barcodeTimer) {
        clearTimeout(barcodeTimer);
    }
    barcodeTimer = setTimeout(clearBarcode, 500);
    if (evt.key.length === 1) {
        if (evt.key === "~") {
            barcode = "~";
        } else if (barcode[0] === "~") {
            barcode = barcode + evt.key;
        }
    }
    if (barcode.length == 7) {
        scanned_barcode = barcode;
        lookupAttendee();
        barcode = "";
    }
}

window.addEventListener('keydown', handleBarcode);

document.addEventListener('DOMContentLoaded', function() {
    if (Cookies.get('secretkey') != undefined) {
        secretkey = Cookies.get('secretkey');
    } else {
        mode = "secret";
        refreshInterface();
    }
}, false);

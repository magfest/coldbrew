var barcode = "";
var barcodeTimer;
var interfaceTimer;
var account = {};
var funds = "";
var secretkey = "";
var mode = "scanning"
var current = document.querySelector(".current");
var icon = document.querySelector(".icon");

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
                    mode = "pouring";
                    refreshInterface();
                } else {
                    mode = "failed";
                    refreshInterface();
                    M.toast({html: data.error});
                }
            }
            else {
                M.toast({html: "Failed to request pour: Server returned "+this.status});
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
        lookupAttendee(barcode);
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
        icon.style.color = "grey";
    } else if (mode === "status") {
        current.innerHTML = "<div><div class='name'>"+account.name+"</div><div class='funds'>&#36;"+funds+"</div><div><i onclick='resetMode()' class='left large material-icons'>clear</i><i onclick='pourDrink()' class='right large material-icons'>send</i></div></div>";
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
        interfaceTimer = setTimeout(resetMode, 2000);
    } else if (mode === "secret") {
        current.innerHTML = '<div><input id="hex" type="text"></div>';
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
                M.toast({html: data.error});
            }
        }
        else {
            M.toast({html: "Failed to lookup account: Server returned "+this.status});
        }
    }
    if (barcode) {
        xhr.send(JSON.stringify({barcode: barcode}));
    }
    else if (account.id) {
        xhr.send(JSON.stringify({id: account.id}));
    }
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

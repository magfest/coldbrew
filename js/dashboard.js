var barcode = "";
var barcodeTimer;
var interfaceTimer;
var account = {};
var funds = "";
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
        xhr.open("POST", "/api/transactions/create", true);
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
        xhr.send(JSON.stringify({account: account.id, amount: -200, note: "Poured a Coldbrew"}));
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
                console.log("Found attendee");
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
        // TODO: Use "barcode" instead of "~ZX1ffQ"
        // Hardcoded to Mark's barcode 
        barcode = "~ZX1ffQ";
        lookupAttendee();
        barcode = "";
    }
}

window.addEventListener('keydown', handleBarcode);
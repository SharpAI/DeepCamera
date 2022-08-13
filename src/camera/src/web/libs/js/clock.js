$(document).ready(function() {
    var monthNames = [ "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December" ]; 
    var dayNames= ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

    var newDate = new Date();
    newDate.setDate(newDate.getDate());
    $('#time-date').html(dayNames[newDate.getDay()] + " " + newDate.getDate() + ' ' + monthNames[newDate.getMonth()] + ' ' + newDate.getFullYear());

    var second=function() {
	   var seconds = new Date().getSeconds();
	   document.getElementById("time-sec").innerHTML=( seconds < 10 ? "0" : "" ) + seconds;
	}
    var minute=function() {
    	var minutes = new Date().getMinutes();
        document.getElementById("time-min").innerHTML=(( minutes < 10 ? "0" : "" ) + minutes);
    }
    var hour=function() {
        var hours = new Date().getHours();
        var element=$("#time-hours");
        hours = ( hours < 10 ? "0" : "" ) + hours;
        if(element.hasClass('twentyfour')&&hours>12){hours=hours-12}
        element.html(hours);
    }
    setInterval(function(){second(),minute(),hour();},1000);
    second(),minute(),hour();
}); 
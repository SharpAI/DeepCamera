process.on('uncaughtException', function (err) {
    console.error('Uncaught Exception occured!');
    console.error(err.stack);
});
var configLocation = __dirname+'/../conf.json';
var fs = require('fs');
var jsonfile = require("jsonfile");
var config = jsonfile.readFileSync(configLocation);
var processArgv = process.argv.splice(2,process.argv.length)
var arguments = {};
processArgv.forEach(function(val) {
    var theSplit = val.split('=');
    var index = theSplit[0];
    var value = theSplit[1];
    if(value==='DELETE'){
        delete(config[index])
    }else{
        try{
            config[index] = JSON.parse(value);
        }catch(err){
            config[index] = value;
        }
    }
    console.log(index + ': ' + value);
});

jsonfile.writeFile(configLocation,config,{spaces: 2},function(){
    console.log('Changes Complete. Here is what it is now.')
    console.log(JSON.stringify(config,null,2))
})
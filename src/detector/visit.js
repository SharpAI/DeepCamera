
function visit(old) {
  var array=[]
  for(a in old){
   array.push([a,old[a]])
  }
  array.sort(function(a,b){return a[1] - b[1]})
  array.reverse()
  return array;
}

module.exports = visit;

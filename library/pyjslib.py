# Copyright 2006 James Tauber and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# iteration from Bob Ippolito's Iteration in JavaScript

from __pyjamas__ import JS

# must declare import _before_ importing sys

def import_module(parent_module, module_name, dynamic=1, async=False):
    """ 
    """

    JS("""
        if (((sys.overrides != null) && 
             (sys.overrides.has_key(module_name))))
        {
            var cache_file =  ( sys.overrides.__getitem__(module_name) + '.cache.js' ) ;
        }
        else
        {
            var cache_file =  ( module_name + '.cache.js' ) ;
        }

        /* already loaded? */
        if (module_load_request[module_name])
        {
            if (module_load_request[module_name] >= 3 && parent_module != null
                && module_name != 'pyjamas')
            {
                //onload_fn = parent_module + '.' + module_name + ' = ' + module_name + ';';
                //pyjs_eval(onload_fn); /* set up the parent-module namespace */
            }
            return;
        }
        module_load_request[module_name] = 1;

        /* following a load, this first executes the script 
         * "preparation" function MODULENAME_loaded_fn()
         * and then sets up the loaded module in the namespace
         * of the parent.
         */

        onload_fn = ''; // module_name + "_loaded_fn();"

        if (module_name != 'pyjamas' && parent_module != null)
        {
            //onload_fn += parent_module + '.' + module_name + ' = ' + module_name + ';';
            /*pmod = parent_module + '.' + module_name;
            onload_fn += 'alert("' + pmod + '"+' + pmod+');';*/
        }


        if (dynamic)
        {
            /* this one tacks the script onto the end of the DOM
             */

            pyjs_load_script(cache_file, onload_fn, async);

            /* this one actually RUNS the script (eval) into the page.
               my feeling is that this would be better for non-async
               but i can't get it to work entirely yet.
             */
            /*pyjs_ajax_eval(cache_file, onload_fn, async);*/
        }
        else
        {
            if (module_name != "pyjslib" &&
                module_name != "sys")
                pyjs_eval(onload_fn);
        }

    """)

JS("""
function import_wait(proceed_fn, dynamic) {

    var timeoutperiod = 100;
    if (dynamic)
        var timeoutperiod = 1;

    var wait = function() {

        var status = '';
        for (l in module_load_request)
        {
            var m = module_load_request[l];
            status += l + m + " ";
        }

        //alert("import wait " + wait_count + " " + status);
        wait_count += 1;

        if (status == '')
        {
            setTimeout(wait, timeoutperiod);
            return;
        }

        for (l in module_load_request)
        {
            if (l == "sys")
                continue
            if (l == "pyjslib")
                continue

            var m = module_load_request[l];
            if (m == 1 || m == 2)
            {
                setTimeout(wait, timeoutperiod);
                return;
            }
            if (m == 3)
            {
                //alert("waited for module " + l + ": loaded");
                module_load_request[l] = 4;
                if (l != 'pyjamas')
                {
                    mod_fn = modules[l];
                }
            }
        }
        //alert("module wait done");

        proceed_fn();
    }

    wait();
}
""")

class Object:
    pass

class Modload:

    def __init__(self, app_modlist, app_imported_fn, dynamic):
        self.app_modlist = app_modlist
        self.app_imported_fn = app_imported_fn
        self.idx = 0;
        self.dynamic = dynamic

    def next(self):
        
        for i in range(len(self.app_modlist[self.idx])):
            app = self.app_modlist[self.idx][i]
            import_module(None, app, self.dynamic, True);
        self.idx += 1

        if self.idx == len(self.app_modlist):
            import_wait(self.app_imported_fn, self.dynamic)
        else:
            import_wait(getattr(self, "next"), self.dynamic)

def preload_app_modules(app_modnames, app_imported_fn, dynamic):

    loader = Modload(app_modnames, app_imported_fn, dynamic)
    loader.next()

import sys

class BaseException:

    name = "BaseException"

    def __init__(self, *args):
        self.args = args

    def toString(self):
        return str(self)

class Exception(BaseException):

    name = "Exception"

class StandardError(Exception):
    name = "StandardError"

class LookupError(StandardError):
    name = "LookupError"

    def toString(self):
        return self.name + ": " + self.args[0]

class KeyError(LookupError):
    name = "KeyError"

class AttributeError(StandardError):

    name = "AttributeError"

    def toString(self):
        return "AttributeError: %s of %s" % (self.args[1], self.args[0])

JS("""
StopIteration = function () {};
StopIteration.prototype = new Error();
StopIteration.name = 'StopIteration';
StopIteration.message = 'StopIteration';

TypeError = function () {};
TypeError.prototype = new Error();
TypeError.name = "TypeError";
TypeError.message = "TypeError";

pyjslib.String_find = function(sub, start, end) {
    var pos=this.indexOf(sub, start);
    if (pyjslib.isUndefined(end)) return pos;

    if (pos + sub.length>end) return -1;
    return pos;
}

pyjslib.String_join = function(data) {
    var text="";

    if (pyjslib.isArray(data)) {
        return data.join(this);
    }
    else if (pyjslib.isIteratable(data)) {
        var iter=data.__iter__();
        try {
            text+=iter.next();
            while (true) {
                var item=iter.next();
                text+=this + item;
            }
        }
        catch (e) {
            if (e != StopIteration) throw e;
        }
    }

    return text;
}

pyjslib.String_isdigit = function() {
    return (this.match(/^\d+$/g) != null);
}

pyjslib.String_replace = function(old, replace, count) {
    var do_max=false;
    var start=0;
    var new_str="";
    var pos=0;

    if (!pyjslib.isString(old)) return this.__replace(old, replace);
    if (!pyjslib.isUndefined(count)) do_max=true;

    while (start<this.length) {
        if (do_max && !count--) break;

        pos=this.indexOf(old, start);
        if (pos<0) break;

        new_str+=this.substring(start, pos) + replace;
        start=pos+old.length;
    }
    if (start<this.length) new_str+=this.substring(start);

    return new_str;
}

pyjslib.String_split = function(sep, maxsplit) {
    var items=new pyjslib.List();
    var do_max=false;
    var subject=this;
    var start=0;
    var pos=0;

    if (pyjslib.isUndefined(sep) || pyjslib.isNull(sep)) {
        sep=" ";
        subject=subject.strip();
        subject=subject.replace(/\s+/g, sep);
    }
    else if (!pyjslib.isUndefined(maxsplit)) do_max=true;

    while (start<subject.length) {
        if (do_max && !maxsplit--) break;

        pos=subject.indexOf(sep, start);
        if (pos<0) break;

        items.append(subject.substring(start, pos));
        start=pos+sep.length;
    }
    if (start<subject.length) items.append(subject.substring(start));

    return items;
}

pyjslib.String___iter__ = function() {
    var i = 0;
    var s = this;
    return {
        'next': function() {
            if (i >= s.length) {
                throw StopIteration;
            }
            return s.substring(i++, i, 1);
        },
        '__iter__': function() {
            return this;
        }
    };
}

pyjslib.String_strip = function(chars) {
    return this.lstrip(chars).rstrip(chars);
}

pyjslib.String_lstrip = function(chars) {
    if (pyjslib.isUndefined(chars)) return this.replace(/^\s+/, "");

    return this.replace(new RegExp("^[" + chars + "]+"), "");
}

pyjslib.String_rstrip = function(chars) {
    if (pyjslib.isUndefined(chars)) return this.replace(/\s+$/, "");

    return this.replace(new RegExp("[" + chars + "]+$"), "");
}

pyjslib.String_startswith = function(prefix, start) {
    if (pyjslib.isUndefined(start)) start = 0;

    if (this.substring(start, prefix.length) == prefix) return true;
    return false;
}

pyjslib.abs = Math.abs;

""")

class Class:
    def __init__(self, name):
        self.name = name

    def __str___(self):
        return self.name

def cmp(a,b):
    if hasattr(a, "__cmp__"):
        return a.__cmp__(b)
    elif hasattr(b, "__cmp__"):
        return -b.__cmp__(a)
    if a > b:
        return 1
    elif b > a:
        return -1
    else:
        return 0

def bool(v):
    # this needs to stay in native code without any dependencies here,
    # because this is used by if and while, we need to prevent
    # recursion
    JS("""
    if (!v) return false;
    switch(typeof v){
    case 'boolean':
        return v;
    case 'object':
        if (v.__nonzero__){
            return v.__nonzero__();
        }else if (v.__len__){
            return v.__len__()>0;
        }
        return true;
    }
    return Boolean(v);
    """)

class List:
    def __init__(self, data=None):
        JS("""
        this.l = [];

        if (pyjslib.isArray(data)) {
            for (var i=0; i < data.length; i++) {
                this.l[i]=data[i];
                }
            }
        else if (pyjslib.isIteratable(data)) {
            var iter=data.__iter__();
            var i=0;
            try {
                while (true) {
                    var item=iter.next();
                    this.l[i++]=item;
                    }
                }
            catch (e) {
                if (e != StopIteration) throw e;
                }
            }
        """)

    def append(self, item):
        JS("""    this.l[this.l.length] = item;""")

    def remove(self, value):
        JS("""
        var index=this.index(value);
        if (index<0) return false;
        this.l.splice(index, 1);
        return true;
        """)

    def index(self, value, start=0):
        JS("""
        var length=this.l.length;
        for (var i=start; i<length; i++) {
            if (this.l[i]==value) {
                return i;
                }
            }
        return -1;
        """)

    def insert(self, index, value):
        JS("""    var a = this.l; this.l=a.slice(0, index).concat(value, a.slice(index));""")

    def pop(self, index = -1):
        JS("""
        if (index<0) index = this.l.length + index;
        var a = this.l[index];
        this.l.splice(index, 1);
        return a;
        """)

    def slice(self, lower, upper):
        JS("""
        if (upper==null) return pyjslib.List(this.l.slice(lower));
        return pyjslib.List(this.l.slice(lower, upper));
        """)

    def __getitem__(self, index):
        JS("""
        if (index<0) index = this.l.length + index;
        return this.l[index];
        """)

    def __setitem__(self, index, value):
        JS("""    this.l[index]=value;""")

    def __delitem__(self, index):
        JS("""    this.l.splice(index, 1);""")

    def __len__(self):
        JS("""    return this.l.length;""")

    def __contains__(self, value):
        return self.index(value) >= 0

    def __iter__(self):
        JS("""
        var i = 0;
        var l = this.l;
        return {
            'next': function() {
                if (i >= l.length) {
                    throw StopIteration;
                }
                return l[i++];
            },
            '__iter__': function() {
                return this;
            }
        };
        """)

    def reverse(self):
        JS("""    this.l.reverse();""")

    def sort(self, compareFunc=None, keyFunc=None, reverse=False):
        if not compareFunc:
            global cmp
            compareFunc = cmp
        if keyFunc and reverse:
            def thisSort1(a,b):
                return -compareFunc(keyFunc(a), keyFunc(b))
            self.l.sort(thisSort1)
        elif keyFunc:
            def thisSort2(a,b):
                return compareFunc(keyFunc(a), keyFunc(b))
            self.l.sort(thisSort2)
        elif reverse:
            def thisSort3(a,b):
                return -compareFunc(a, b)
            self.l.sort(thisSort3)
        else:
            self.l.sort(compareFunc)

    def getArray(self):
        """
        Access the javascript Array that is used internally by this list
        """
        return self.l

list = List

class Tuple(List):
    def __init__(self, data):
        List.__init__(self, data)

tuple = Tuple


class Dict:
    def __init__(self, data=None):
        JS("""
        this.d = {};

        if (pyjslib.isArray(data)) {
            for (var i in data) {
                var item=data[i];
                this.__setitem__(item[0], item[1]);
                //var sKey=pyjslib.hash(item[0]);
                //this.d[sKey]=item[1];
                }
            }
        else if (pyjslib.isIteratable(data)) {
            var iter=data.__iter__();
            try {
                while (true) {
                    var item=iter.next();
                    this.__setitem__(item.__getitem__(0), item.__getitem__(1));
                    }
                }
            catch (e) {
                if (e != StopIteration) throw e;
                }
            }
        else if (pyjslib.isObject(data)) {
            for (var key in data) {
                this.__setitem__(key, data[key]);
                }
            }
        """)

    def __setitem__(self, key, value):
        JS("""
        var sKey = pyjslib.hash(key);
        this.d[sKey]=[key, value];
        """)

    def __getitem__(self, key):
        JS("""
        var sKey = pyjslib.hash(key);
        var value=this.d[sKey];
        if (pyjslib.isUndefined(value)){
            throw pyjslib.KeyError(key);
        }
        return value[1];
        """)

    def __nonzero__(self):
        JS("""
        for (var i in this.d){
            return true;
        }
        return false;
        """)

    def __len__(self):
        JS("""
        var size=0;
        for (var i in this.d) size++;
        return size;
        """)

    def has_key(self, key):
        return self.__contains__(key)

    def __delitem__(self, key):
        JS("""
        var sKey = pyjslib.hash(key);
        delete this.d[sKey];
        """)

    def __contains__(self, key):
        JS("""
        var sKey = pyjslib.hash(key);
        return (pyjslib.isUndefined(this.d[sKey])) ? false : true;
        """)

    def keys(self):
        JS("""
        var keys=new pyjslib.List();
        for (var key in this.d) {
            keys.append(this.d[key][0]);
        }
        return keys;
        """)

    def values(self):
        JS("""
        var values=new pyjslib.List();
        for (var key in this.d) values.append(this.d[key][1]);
        return values;
        """)

    def items(self):
        JS("""
        var items = new pyjslib.List();
        for (var key in this.d) {
          var kv = this.d[key];
          items.append(new pyjslib.List(kv))
          }
          return items;
        """)

    def __iter__(self):
        return self.keys().__iter__()

    def iterkeys(self):
        return self.__iter__()

    def itervalues(self):
        return self.values().__iter__();

    def iteritems(self):
        return self.items().__iter__();

    def setdefault(self, key, default_value):
        if not self.has_key(key):
            self[key] = default_value

    def get(self, key, default_=None):
        if not self.has_key(key):
            return default_
        return self[key]

    def update(self, d):
        for k,v in d.iteritems():
            self[k] = v

    def getObject(self):
        """
        Return the javascript Object which this class uses to store
        dictionary keys and values
        """
        return self.d

    def copy(self):
        return Dict(self.items())

dict = Dict

# taken from mochikit: range( [start,] stop[, step] )
def range():
    JS("""
    var start = 0;
    var stop = 0;
    var step = 1;

    if (arguments.length == 2) {
        start = arguments[0];
        stop = arguments[1];
        }
    else if (arguments.length == 3) {
        start = arguments[0];
        stop = arguments[1];
        step = arguments[2];
        }
    else if (arguments.length>0) stop = arguments[0];

    return {
        'next': function() {
            if ((step > 0 && start >= stop) || (step < 0 && start <= stop)) throw StopIteration;
            var rval = start;
            start += step;
            return rval;
            },
        '__iter__': function() {
            return this;
            }
        }
    """)

def slice(object, lower, upper):
    JS("""
    if (pyjslib.isString(object)) {
        if (lower < 0) {
           lower = object.length + lower;
        }
        if (upper < 0) {
           upper = object.length + upper;
        }
        if (pyjslib.isNull(upper)) upper=object.length;
        return object.substring(lower, upper);
    }
    if (pyjslib.isObject(object) && object.slice)
        return object.slice(lower, upper);

    return null;
    """)

def str(text):
    JS("""
    return String(text);
    """)

def ord(x):
    if(isString(x) and len(x) == 1):
        JS("""
            return x.charCodeAt(0);
        """)
    else:
        JS("""
            throw TypeError;
        """)
    return None

def chr(x):
    JS("""
        return String.fromCharCode(x)
    """)

def is_basetype(x):
    JS("""
       var t = typeof(x);
       return t == 'boolean' ||
       t == 'function' ||
       t == 'number' ||
       t == 'string' ||
       t == 'undefined'
       ;
    """)

def get_pyjs_classtype(x):
    JS("""
       if (pyjslib.hasattr(x, "__class__"))
           if (pyjslib.hasattr(x.__class__, "__new__"))
               var src = x.__class__.__name__;
               return src;
       return null;
    """)

def repr(x):
    """ Return the string representation of 'x'.
    """
    JS("""
       if (x === null)
           return "null";

       if (x === undefined)
           return "undefined";

       var t = typeof(x);

       if (t == "boolean")
           return x.toString();

       if (t == "function")
           return "<function " + x.toString() + ">";

       if (t == "number")
           return x.toString();

       if (t == "string") {
           if (x.indexOf('"') == -1)
               return '"' + x + '"';
           if (x.indexOf("'") == -1)
               return "'" + x + "'";
           var s = x.replace(new RegExp('"', "g"), '\\\\"');
           return '"' + s + '"';
       };

       if (t == "undefined")
           return "undefined";

       // If we get here, x is an object.  See if it's a Pyjamas class.

       if (!pyjslib.hasattr(x, "__init__"))
           return "<" + x.toString() + ">";

       // Handle the common Pyjamas data types.

       var constructor = "UNKNOWN";

       constructor = pyjslib.get_pyjs_classtype(x);

       if (constructor == "pyjslib.Tuple") {
           var contents = x.getArray();
           var s = "(";
           for (var i=0; i < contents.length; i++) {
               s += pyjslib.repr(contents[i]);
               if (i < contents.length - 1)
                   s += ", ";
           };
           s += ")"
           return s;
       };

       if (constructor == "pyjslib.List") {
           var contents = x.getArray();
           var s = "[";
           for (var i=0; i < contents.length; i++) {
               s += pyjslib.repr(contents[i]);
               if (i < contents.length - 1)
                   s += ", ";
           };
           s += "]"
           return s;
       };

       if (constructor == "pyjslib.Dict") {
           var keys = new Array();
           for (var key in x.d)
               keys.push(key);

           var s = "{";
           for (var i=0; i<keys.length; i++) {
               var key = keys[i]
               s += pyjslib.repr(key) + ": " + pyjslib.repr(x.d[key]);
               if (i < keys.length-1)
                   s += ", "
           };
           s += "}";
           return s;
       };

       // If we get here, the class isn't one we know -> return the class name.
       // Note that we replace underscores with dots so that the name will
       // (hopefully!) look like the original Python name.

       var s = constructor.replace(new RegExp('_', "g"), '.');
       return "<" + s + " object>";
    """)

def int(text, radix=0):
    JS("""
    return parseInt(text, radix);
    """)

def len(object):
    JS("""
    if (object==null) return 0;
    if (pyjslib.isObject(object) && object.__len__) return object.__len__();
    return object.length;
    """)

def isinstance(object_, classinfo):
    if _isinstance(classinfo, Tuple):
        for ci in classinfo:
            if isinstance(object_, ci):
                return True
        return False
    else:
        return _isinstance(object_, classinfo)

def _isinstance(object_, classinfo):
    JS("""
    if (object_.__class__){
        var res =  object_ instanceof classinfo.constructor;
        return res;
    }
    return false;
    """)

def getattr(obj, name, default_):
    JS("""
    if ((!pyjslib.isObject(obj))||(pyjslib.isUndefined(obj[name]))){
        if (pyjslib.isUndefined(default_)){
            throw pyjslib.AttributeError(obj, name);
        }else{
        return default_;
        }
    }
    if (!pyjslib.isFunction(obj[name])) return obj[name];
   return function() {
        var args = [];
        for (var i = 0; i < arguments.length; i++) {
          args.push(arguments[i]);
        }
        return obj[name].apply(obj,args);
        }
    """)

def setattr(obj, name, value):
    JS("""
    if (!pyjslib.isObject(obj)) return null;

    obj[name] = value;

    """)

def hasattr(obj, name):
    JS("""
    if (!pyjslib.isObject(obj)) return false;
    if (pyjslib.isUndefined(obj[name])) return false;

    return true;
    """)

def dir(obj):
    JS("""
    var properties=new pyjslib.List();
    for (property in obj) properties.append(property);
    return properties;
    """)

def filter(obj, method, sequence=None):
    # object context is LOST when a method is passed, hence object must be passed separately
    # to emulate python behaviour, should generate this code inline rather than as a function call
    items = []
    if sequence == None:
        sequence = method
        method = obj

        for item in sequence:
            if method(item):
                items.append(item)
    else:
        for item in sequence:
            if method.call(obj, item):
                items.append(item)

    return items


def map(obj, method, sequence=None):
    items = []

    if sequence == None:
        sequence = method
        method = obj

        for item in sequence:
            items.append(method(item))
    else:
        for item in sequence:
            items.append(method.call(obj, item))

    return items


def enumerate(sequence):
    enumeration = []
    nextIndex = 0
    for item in sequence:
        enumeration.append([nextIndex, item])
        nextIndex = nextIndex + 1
    return enumeration


def min(sequence):
    minValue = None
    for item in sequence:
        if minValue == None:
            minValue = item
        elif item < minValue:
            minValue = item
    return minValue


def max(sequence):
    maxValue = None
    for item in sequence:
        if maxValue == None:
            maxValue = item
        elif item > maxValue:
            maxValue = item
    return maxValue


next_hash_id = 0

def hash(obj):
    JS("""
    if (obj == null) return null;

    if (obj.$H) return obj.$H;
    if (obj.__hash__) return obj.__hash__();
    if (obj.constructor == String || obj.constructor == Number || obj.constructor == Date) return obj;

    obj.$H = ++pyjslib.next_hash_id;
    return obj.$H;
    """)


# type functions from Douglas Crockford's Remedial Javascript: http://www.crockford.com/javascript/remedial.html
def isObject(a):
    JS("""
    return (a && typeof a == 'object') || pyjslib.isFunction(a);
    """)

def isFunction(a):
    JS("""
    return typeof a == 'function';
    """)

def isString(a):
    JS("""
    return typeof a == 'string';
    """)

def isNull(a):
    JS("""
    return typeof a == 'object' && !a;
    """)

def isArray(a):
    JS("""
    return pyjslib.isObject(a) && a.constructor == Array;
    """)

def isUndefined(a):
    JS("""
    return typeof a == 'undefined';
    """)

def isIteratable(a):
    JS("""
    return pyjslib.isObject(a) && a.__iter__;
    """)

def isNumber(a):
    JS("""
    return typeof a == 'number' && isFinite(a);
    """)

def toJSObjects(x):
    """
       Convert the pyjs pythonic List and Dict objects into javascript Object and Array
       objects, recursively.
    """
    if isArray(x):
        JS("""
        var result = [];
        for(var k=0; k < x.length; k++) {
           var v = x[k];
           var tv = pyjslib.toJSObjects(v);
           result.push(tv);
        }
        return result;
        """)
    if isObject(x):
        if isinstance(x, Dict):
            JS("""
            var o = x.getObject();
            var result = {};
            for (var i in o) {
               result[o[i][0].toString()] = o[i][1];
            }
            return pyjslib.toJSObjects(result)
            """)
        elif isinstance(x, List):
            return toJSObjects(x.l)
        elif hasattr(x, '__class__'):
            # we do not have a special implementation for custom
            # classes, just pass it on
            return x
    if isObject(x):
        JS("""
        var result = {};
        for(var k in x) {
            var v = x[k];
            var tv = pyjslib.toJSObjects(v)
            result[k] = tv;
            }
            return result;
         """)
    return x

def printFunc(objs):
    JS("""
    if ($wnd.console==undefined)  return;
    var s = "";
    for(var i=0; i < objs.length; i++) {
        if(s != "") s += " ";
        s += objs[i];
    }
    console.debug(s)
    """)


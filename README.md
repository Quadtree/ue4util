Run this in the root of your project:

    python3 '{{path to this project}}\watch.py'

Directives:

* `extends(parentName)` - Putting one of these in a cpp file indicates this is a class. The U/A etc will be derived from the parent name.
* `im(className)` - Imports the given class. Doesn't actually do anything, as classes appearing are always imported by default.
* `blueprintEvent(functionName)` - Creates a new member that is a blueprint implementable event.
* `prop(mods type propertyName)` - Creates a new property. Mods are the usual ones like BlueprintReadWrite or something. There are a few special ones:
  * `bare` - Do not define this a UPROPERTY
* `classMods(mods)` - What modifications to apply to the class. Space separated
* `fun` - Goes in function definitions like `mods(...) void fun::someFunction(){ ... }`
  * Note that if this function calls Super:: in its body, it will be automatically defined as "override"
  * Mods can be:
    * `bare`: Do not set UFUNCTION
    * `virtual`: Set virtual on function definition
    * Any normal UFUNCTION modifier
    * Mods should be space separated

Using in MSVC:

Create a script like this:

    #/bin/sh
    python3 'F:\Data\Documents\scripts\ue4util\watch.py'

Run it like this

    ./watch.sh &

Stop it like this

    kill %1

After creating a function, MSVC will not immediately recognize it. To force intellisense to re-enumerate the members of the class, put your cursor right after the fun:: and press Ctrl+Space. After a few moments, it should recognize the new function.

If this technique doesn't work (seems very inconsistent), try putting your cursor on the newly created thing and pressing Ctrl+F12 or F12. This only seems to work reliably on functions, though. For variables, you need to do "this->X".
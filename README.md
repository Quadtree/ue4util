# Running
Run this in the root of your project:

    #/bin/sh
    python3 '{{path to this project}}\watch.py'

Run it by double clicking on it in Windows Explorer, assuming you have Cygwin set up to run .sh files.

Add this to your build.cs file:

    PublicIncludePaths.Add("{{{ProjectName}}}/Public");

If you don't want to commit the .prebuild data files (they can be regenerated at any time with this tool), add this to your .gitignore:

    .prebuild*
    Source/{{{ProjectName}}}/Public

## Using in MSVC
After creating a function, MSVC will not immediately recognize it. To force intellisense to re-enumerate the members of the class, right click and select Rescan -> Rescan File. Since you will be doing this a lot, it's a good idea to bind it to a key. I've used F7 for this purpose.

# Directives

## Header
At the top of each .cpp file using this, put this:

```cpp
#include "Y.h"
#include "X.h"
#include "X.ac.h"
```

Where "X" is the .cpp filename, without the .cpp, and "Y" is the name of the project.

## Classes
* `extends(parentName)` - Putting one of these in a cpp file indicates this is a class. The U/A etc will be derived from the parent name. Note that the value of "FStruct" is special. This denotes a structure with no superclass.
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

## Enums
Create a new .cpp file and put `enumValue(X)` directives, one per line after the usual header.
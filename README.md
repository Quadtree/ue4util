Add this to all your .Target.cs files (replace {{prebuild_loc}} with this directory's location):

    PreBuildSteps.Add("python3 {{prebuild_loc}}\\prebuild.py \"$(TargetName)\" \"$(ProjectDir)\" \"$(EngineDir)\"");
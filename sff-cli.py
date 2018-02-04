import os, sys
import argparse

INJECT_KEYWORD = "--<*"
TEMP_FILENAME  = "tmp.sff"

parser = argparse.ArgumentParser(description='Command line utility for the SuperFastFramework.')
parser.add_argument('-p', '--path', help='Path of the SFF project. Defaults to \'.\' ')
parser.add_argument('-g', '--generate', choices=['state','entity'], help='Generates boiler plate code.')
parser.add_argument('-n', '--name', help='Name of the file to be generated. Use this with --generate flag')
parser.add_argument('-c', '--compile' , metavar='OUTPUT', help='Takes main.lua and all the files it references and generates a .p8 file.')

args = parser.parse_args()

# extension must include the .
# like so: '.lua', '.p8'
def _add_extension(name, extension):
    tmp=name
    if not tmp.endswith(extension):
        tmp+=extension

    return tmp

def compile(path, name):
    os.chdir(path)

    # Add correct extension to the output file name
    out_p8=_add_extension(name, '.p8')

    print("Compiling... ")
    # Generates a tmp.sff with all the code
    with open(path+os.sep+TEMP_FILENAME, 'w') as out_file: # Opens the temp file for writing
        with open(path+'/main.lua') as in_file:         # Opens the main SFF lua file
            line = in_file.readline()
            print("Importing code... ")
            while line:
                # Check for file to inject keyword
                if line.startswith(INJECT_KEYWORD): 
                    filename_to_inject = line.split(INJECT_KEYWORD, 1)[1].strip()

                    try:
                        # Copy the refered file into the out_file
                        with open(filename_to_inject) as file_to_inject:
                            for line in file_to_inject:
                                out_file.write(line)
                        out_file.write("\n") # Avoid pico8 file generation errors
                    except FileNotFoundError:
                        print("ERR - Specified path ('"+path+os.sep+filename_to_inject+"') doesn't exists.", file=sys.stderr)
                        sys.exit(1)

                # Copy line directly into out_file
                else:
                    out_file.write(line)

                line = in_file.readline()
            

        # Copy all assets (music, art, map, sfx) from the .p8 file into TEMP_FILENAME
        try:
            discard=True
            with open(path+os.sep+out_p8) as in_file:
                print("Importing assets... ")
                line = in_file.readline()
                while line:
                    if line.startswith("__gfx__"): # Everything after this tag is an asset
                        discard=False

                    if not discard:
                        out_file.write(line)

                    line = in_file.readline()
        except FileNotFoundError:
            # The .p8 file doesn't exists, so I don't have to copy assets from. I don't care
            print("No previous .p8 file. No assets imported")

    # moves the tmp.sff to the <name>.p8
    os.rename(path+"/"+TEMP_FILENAME, path+"/"+out_p8)
    print("Done!")

def generate_state(path, name):
    template="""-- state
function """+name+"""()
    local s={}
    local updateables={}
    local drawables={}

    s.update=function()
        for u in all(updateables) do
            u:update()
        end
    end

    s.draw=function()
        for d in all(drawables) do
            d:draw()
        end
    end

    return s
end"""
    # Add correct extension to the output file name
    out_lua=_add_extension(name, '.lua')
    
    print("Generating state...")

    # Check if file exists
    file=path + os.sep + out_lua

    if os.path.isfile(file):
        text = input("File '"+file+"' already exists. Overwrite? [y/n] N: ")
        if not text == 'y':
            print("Abort")
            sys.exit(0)

    with open(path+os.sep+out_lua, 'w') as out_file: # Creates the file
        out_file.write(template)

    print("Done!")
    print("Don't forget to add --<*"+name+" to the main.lua file.")

def generate_entity(path, name):
    print("Printing entity boilerplate to stdout...")
    print("")

    template="function "+name+"""(x,y)
    local anim_obj=anim()
    anim:add(first_fr,fr_count,speed,zoomw,zoomh)

    local e=entity(anim_obj)
    e:setpos(x,y)
    e:set_anim(1)

    local bounds_obj=bbox(8,8)
    e:set_bounds(bounds_obj)
    -- e.debugbounds=true

    return e
end
"""
    print(template)


if __name__ == '__main__':
    if(args.generate and args.compile):
        print("ERR - You can't choose to generate a file and compile at the same time.\nRemove either the -c or -g flags.", file=sys.stderr)
        sys.exit(1)

    path=args.path or '.'
    

    if(args.compile):
        try:
            compile(path, args.compile)
        except FileNotFoundError:
            print("ERR - Specified path ('"+path+"') doesn't exists.", file=sys.stderr)

    elif(args.generate):
        if not args.name:
            print("ERR - Name is mandatory: -n/--name NAME", file=sys.stderr)
            sys.exit(1)
        
        if args.generate == "state":
            generate_state(path, args.name)

        elif args.generate == "entity":
            generate_entity(path, args.name)


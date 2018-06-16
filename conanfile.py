import shutil

from conans import ConanFile, CMake
from conans import tools
import os


class SFMLConan(ConanFile):
    name = "SFML"
    version = "2.4.2"
    url = "https://github.com/lasote/conan-sfml.git"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    requires = ("libjpeg/9b@bincrafters/stable", "flac/1.3.2@bincrafters/stable",
                "vorbis/1.3.5@bincrafters/stable", "freetype/2.8.1@bincrafters/stable",
                "stb/20180214@conan/stable")
    generators = "cmake"

    @property
    def folder_name(self):
        return "SFML-%s" % self.version

    def system_requirements(self):
        self.output.info("=================" + tools.os_info.linux_distro)
        if tools.os_info.linux_distro == "ubuntu" or tools.os_info.linux_distro == "linuxmint":
            self.output.info("================= UPDATE")
            tools.SystemPackageTool().update()
            tools.SystemPackageTool().install("libx11-dev libxrandr-dev libglu1-mesa-dev libudev-dev xorg-dev libtool automake")

    def requirements(self):
        if self.settings.os == "Linux":
            self.requires("openal/1.18.2@bincrafters/stable")
        elif self.settings.os == "Macos":
            self.requires("libjpeg/9b@bincrafters/stable")
            self.requires("flac/1.3.2@bincrafters/stable")
            self.requires("vorbis/1.3.5@bincrafters/stable")
            self.requires("freetype/2.8.1@bincrafters/stable")
            self.requires("stb/73990fe@conan/testing")

    def source(self):
        tools.download("https://github.com/SFML/SFML/archive/%s.zip" % self.version, "sfml.zip")
        tools.unzip("sfml.zip")
        os.unlink("sfml.zip")
        shutil.rmtree(os.path.join(self.folder_name, "extlibs"))
        tools.replace_in_file(os.path.join(self.folder_name, "CMakeLists.txt"),
                              "project(SFML)",
                              """project(SFML)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()
""")
        # Link errors of freetype missing bzip2 and libpng
        tools.replace_in_file(os.path.join(self.folder_name, "src",
                                           "SFML", "Graphics", "CMakeLists.txt"),
                              "EXTERNAL_LIBS ${GRAPHICS_EXT_LIBS}",
                              "EXTERNAL_LIBS ${CONAN_LIBS}")

        if self.settings.os == "Linux":  # find flac not working on ubuntu
            path = os.path.join(self.folder_name, "src", "SFML", "Audio", "CMakeLists.txt")
            flag_lib = self.deps_cpp_info["flac"].libs[0]
            tools.replace_in_file(path,
                                  "find_package(FLAC REQUIRED)",
                                  'set(FLAC_LIBRARY "%s")' % flag_lib)


    def build(self):
        cmake = CMake(self)
        if self.settings.compiler == "Visual Studio":
            cmake.definitions["SFML_USE_STATIC_STD_LIBS"] = "ON" if "MD" not in str(self.settings.compiler.runtime) else "OFF"
        cmake.definitions["CMAKE_POSITION_INDEPENDENT_CODE"] = "ON"
        cmake.definitions["BUILD_SHARED_LIBS"] = "ON" if self.options.shared else "OFF"
        if self.options.shared == False:
            cmake.definitions["SFML_STATIC_LIBRARIES"] = "ON"
        cmake.definitions["SFML_BUILD_EXAMPLES"] = "OFF"
        cmake.definitions["SFML_BUILD_DOC"] = "OFF"
        cmake.verbose = True
        cmake.parallel = True
        cmake.configure(source_folder=os.path.join(self.source_folder, self.folder_name))
        cmake.build()

    def package(self):
        self.copy("*.hpp", src="%s/include" % self.folder_name, dst="include", keep_path=True)
        self.copy("*.inl", src="%s/include" % self.folder_name, dst="include", keep_path=True)

        # But for libs and dlls, we want to avoid intermediate folders
        self.copy(pattern="*.lib", dst="lib", src="lib", keep_path=False)
        self.copy(pattern="*.a",   dst="lib", src="lib", keep_path=False)

        if self.options.shared:
            self.copy(pattern="*.dll", dst="bin", src="bin", keep_path=False)
            # in linux shared libs are in lib, not bin
            self.copy(pattern="*.so*", dst="lib", src="lib", keep_path=False, symlinks=True)
            self.copy(pattern="*.dylib*", dst="lib", src="lib", keep_path=False, symlinks=True)

    def package_info(self):
        libs = tools.collect_libs(self)
        self.cpp_info.libs = libs
        if tools.os_info.linux_distro == "ubuntu" or tools.os_info.linux_distro == "linuxmint":
            self.cpp_info.libs.append("udev")
            self.cpp_info.libs.append("GL")
            self.cpp_info.libs.append("GLU")
            self.cpp_info.libs.append("Xrandr")
            self.cpp_info.libs.append("X11")
            self.cpp_info.libs.append("-ludev -lGL -lGLU -lXrandr -lX11")
        if tools.os_info.is_macos:
            self.cpp_info.exelinkflags.append("-framework Cocoa")
            self.cpp_info.exelinkflags.append("-framework OpenGL")
            self.cpp_info.exelinkflags.append("-framework OpenAL")
            self.cpp_info.exelinkflags.append("-framework IOKit")
            self.cpp_info.exelinkflags.append("-framework Carbon")

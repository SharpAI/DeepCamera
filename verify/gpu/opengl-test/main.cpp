#include <string>
#include <iostream>
#include <fstream>
#include <GLFW/glfw3.h>
#include <GLES3/gl3.h>
#include <GLES3/gl3ext.h>
#include <cassert>

namespace gl {

inline const char *GLGetErrorString(GLenum error) {
  switch (error) {
    case GL_NO_ERROR:
      return "GL_NO_ERROR";
    case GL_INVALID_ENUM:
      return "GL_INVALID_ENUM";
    case GL_INVALID_VALUE:
      return "GL_INVALID_VALUE";
    case GL_INVALID_OPERATION:
      return "GL_INVALID_OPERATION";
    //case GL_STACK_OVERFLOW:
    //  return "GL_STACK_OVERFLOW";
    //case GL_STACK_UNDERFLOW:
    //  return "GL_STACK_UNDERFLOW";
    case GL_OUT_OF_MEMORY:
      return "GL_OUT_OF_MEMORY";
    default:
      return "Unknown OpenGL error code";
  }
}

}  // namespace gl

// TODO(zhixunt): When porting to TVM, change this to
//   CHECK(err == GL_NO_ERROR) << ...;
void OPENGL_CHECK_ERROR() {
  GLenum err = glGetError();
  if (err != GL_NO_ERROR) {
    std::cerr << "OpenGL error, code=" << err << ": "
              << gl::GLGetErrorString(err);
    assert(false);
  }
}

/*!
 * \brief Protected OpenGL call.
 * \param func Expression to call.
 */
#define OPENGL_CALL(func)                                                      \
  {                                                                            \
    (func);                                                                    \
    OPENGL_CHECK_ERROR();                                                      \
  }

void GlfwErrorCallback(int err, const char *str) {
  std::cerr << "Error: [" << err << "] " << str << std::endl;
}

// Don't need to change this.
// We want to draw 2 giant triangles that cover the whole screen.
struct Vertex {
  float x, y;
};
Vertex vertices[] = {
    {-1.f, -1.f},
    {1.0f, -1.f},
    {1.0f, 1.0f},
    {-1.f, -1.f},
    {-1.f, 1.0f},
    {1.0f, 1.0f},
};

// Don't need to change this.
// The vertex shader only needs to take in the triangle points.
// No need for point transformations.
static const char *vertex_shader_text =
    "#version 120\n"
    "attribute vec2 point; // input to vertex shader\n"
    "void main() {\n"
    "  gl_Position = vec4(point, 0.0, 1.0);\n"
    "}\n";

// This is the main part.
static const char *fragment_shader_text =
    "#version 120\n"
    "uniform int width;\n"
    "uniform int height;\n"
    "uniform sampler1D texture0;\n"
    "uniform sampler1D texture1;\n"
    "void main() {\n"
    "  // TODO(zhixunt): Calculate pixel index.\n"
    "  // gl_FragColor = vec4(gl_FragCoord.x / float(width), gl_FragCoord.y / float(height), 0.75, 1.0)\n;"
    "  gl_FragColor = vec4(\n"
    "    texture1D(texture0, 0.0).r + texture1D(texture1, 0.0).r,\n"
    "    0.0,\n"
    "    0.0,\n"
    "    1.0\n"
    "  );\n"
    "}\n";

int main(int argc, char *argv[]) {
  std::cout << "Hello, World!!" << std::endl;

  // Set an error handler.
  // This can be called before glfwInit().
  glfwSetErrorCallback(&GlfwErrorCallback);

  // Initialize GLFW.
  if (glfwInit() != GLFW_TRUE) {
    std::cout << "glfwInit() failed!" << std::endl;
    return 1;
  }

  GLint width = 640;
  GLint height = 480;

  // Create a window.
  // TODO(zhixunt): GLFW allows us to create an invisible window.
  // TODO(zhixunt): On retina display, window size is different from framebuffer size.
  GLFWwindow *window = glfwCreateWindow(width, height, "My Title", nullptr, nullptr);
  if (window == nullptr) {
    std::cout << "glfwCreateWindow() failed!" << std::endl;
    return 1;
  }

  std::cout
      << "OpenGL version: "
      << glfwGetWindowAttrib(window, GLFW_CONTEXT_VERSION_MAJOR)
      << "."
      << glfwGetWindowAttrib(window, GLFW_CONTEXT_VERSION_MINOR)
      << "."
      << glfwGetWindowAttrib(window, GLFW_CONTEXT_REVISION)
      << std::endl;

  // Before using any OpenGL API, we must specify a context.
  glfwMakeContextCurrent(window);

  // Create the vertex shader.
  GLuint vertex_shader = glCreateShader(GL_VERTEX_SHADER);
  OPENGL_CALL(glShaderSource(vertex_shader, 1, &vertex_shader_text, nullptr));
  OPENGL_CALL(glCompileShader(vertex_shader));

  // Create the fragment shader.
  GLuint fragment_shader = glCreateShader(GL_FRAGMENT_SHADER);
  OPENGL_CALL(glShaderSource(fragment_shader, 1, &fragment_shader_text, nullptr));
  OPENGL_CALL(glCompileShader(fragment_shader));

  // Combine the vertex and fragment shaders to create a "program".
  GLuint program = glCreateProgram();
  OPENGL_CALL(glAttachShader(program, vertex_shader));
  OPENGL_CALL(glAttachShader(program, fragment_shader));
  OPENGL_CALL(glLinkProgram(program));
  OPENGL_CALL(glUseProgram(program));

  GLuint vertex_buffer;
  OPENGL_CALL(glGenBuffers(1, &vertex_buffer));
  OPENGL_CALL(glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer));
  OPENGL_CALL(glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW));

  auto point_attrib = static_cast<GLuint>(glGetAttribLocation(program, "point"));
  OPENGL_CALL(glEnableVertexAttribArray(point_attrib));
  OPENGL_CALL(glVertexAttribPointer(point_attrib, 2, GL_FLOAT, GL_FALSE, sizeof(Vertex), nullptr));

  glfwGetFramebufferSize(window, &width, &height);
  auto width_uniform = glGetUniformLocation(program, "width");
  auto height_uniform = glGetUniformLocation(program, "height");
  OPENGL_CALL(glUniform1i(width_uniform, width));
  OPENGL_CALL(glUniform1i(height_uniform, height));
  OPENGL_CALL(glViewport(0, 0, width, height));

  // Set up the first texture.
  // https://www.opengl.org/discussion_boards/showthread.php/174926-when-to-use-glActiveTexture
  // Consider the internal OpenGL texture system as this.
  //   struct TextureUnit {
  //     GLuint target_texture_1D;
  //     GLuint target_texture_2D;
  //     GLuint target_texture_3D;
  //     GLuint target_texture_cube;
  //     ...
  //   };
  //   TextureUnit texture_units[GL_MAX_TEXTURE_IMAGE_UNITS];
  //   GLuint curr_texture_unit; // global state!!!
  //
  // Then:
  //   "glActiveTexture(GL_TEXTURE0);"
  //     <=>
  //   "curr_texture_unit = 0;"
  //
  //   "glBindTexture(GL_TEXTURE_2D, texture0);"
  //     <=>
  //   "texture_units[curr_texture_unit].target_texture_1D = texture0;"
  //
  {
    GLuint texture0;
    GLsizei texture0_width = 100;
    GLfloat texture0_data[100] = {0.5f};

    // Create a texture.
    OPENGL_CALL(glGenTextures(1, &texture0));

    // See comments above.
    OPENGL_CALL(glActiveTexture(GL_TEXTURE0));
    OPENGL_CALL(glBindTexture(GL_TEXTURE_2D, texture0));

    // Similar to cudaMemcpy.
    //OPENGL_CALL(glTexImage1D(GL_TEXTURE_2D, 0, GL_RED, texture0_width, 0, GL_RED, GL_FLOAT, texture0_data));

    // Bind uniform "texture0" to GL_TEXTURE0.
    GLint texture0_uniform = glGetUniformLocation(program, "texture0");
    OPENGL_CALL(glUniform1i(texture0_uniform, 0));

    // TODO(zhixunt): What is this?
    OPENGL_CALL(glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE));
    OPENGL_CALL(glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE));
    OPENGL_CALL(glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR));
    OPENGL_CALL(glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR));
  }

  {
    GLuint texture1;
    GLsizei texture1_width = 100;
    GLfloat texture1_data[100] = {0.5f};
    OPENGL_CALL(glGenTextures(1, &texture1));
    OPENGL_CALL(glActiveTexture(GL_TEXTURE1));
    OPENGL_CALL(glBindTexture(GL_TEXTURE_2D, texture1));
    //OPENGL_CALL(glTexImage1D(GL_TEXTURE_2D, 0, GL_RED, texture1_width, 0, GL_RED, GL_FLOAT, texture1_data));
    GLint texture1_uniform = glGetUniformLocation(program, "texture1");
    OPENGL_CALL(glUniform1i(texture1_uniform, 1));
    OPENGL_CALL(glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE));
    OPENGL_CALL(glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE));
    OPENGL_CALL(glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR));
    OPENGL_CALL(glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR));
  }

  glClear(GL_COLOR_BUFFER_BIT);
  OPENGL_CALL(glDrawArrays(GL_TRIANGLES, 0, 6));
  glfwSwapBuffers(window);

  while (glfwWindowShouldClose(window) == GLFW_FALSE) {
    glfwPollEvents();
  }

  // Paired with glfwCreateWindow().
  glfwDestroyWindow(window);

  // Paired with glfwInit().
  glfwTerminate();

  return 0;
}

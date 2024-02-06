
import modules.scripts as scripts
import modules.shared as shared

import gradio as gr

import PIL.Image as image
import PIL.ImageFilter as filter

import os
import random


allowedexts = ['.png', '.jpg', '.jpeg']
def is_allowed_img_dirent(dirent):
  global allowedexts
  if not dirent.is_file():
    return False
  (root, ext) = os.path.splitext(dirent.path)
  if ext not in allowedexts:
    return False
  return True

class RandomImg2Img(scripts.Script):
    def __init__(self):
        pass

    def title(self):
        return "Random img2img input"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
      with gr.Accordion('Random input images', open=False):
        with gr.Row():
          active = gr.Checkbox(value=False, label="Active", elem_id='img2img_random_active')
          blur_radius = gr.Slider(value=0.0, minimum=0.0, maximum=256.0, step=1.0, label="Blur radius", elem_id='img2img_random_blur_radius', info='If greater than zero, all randomly selected images will be blurred. If an input image is given, it will not be blurred')
        with gr.Row():
          count = gr.Slider(value=1.0, minimum=1.0, maximum=20.0, step=1, label="Blend count", elem_id='img2img_random_count', info='The number of images to load from the given directory. If more than one, they will be blended together using the blend alpha. If a regular input is given, it will be used as the first image in the composite')
          blend_alpha = gr.Slider(value=0.5, minimum=0.0, maximum=1.0, step=0.01, label="Blend alpha", elem_id='img2img_random_blend_alpha', info='The value each successive image is blended into the previous one')
        input_dir = gr.Textbox(label="Input directory", **shared.hide_dirs, elem_id="img2img_random_input_dir", info='The directory to randomly load images from')
      return [active, count, blur_radius, blend_alpha, input_dir]
    

    def process(self, p, active, count, blur_radius, blend_alpha, input_dir, *args, **kwargs):
        if not active:
          return
        
        # get all compatible files in the input directory
        file_choices = [dirent.path for dirent in os.scandir(input_dir) if is_allowed_img_dirent(dirent)]
        if len(file_choices) == 0:
          raise ValueError('No images found in input directory.')
        
        # this seeds the file selection based on the current time
        random.seed()
        
        # composite the selected images, recursively
        selected_files_list = random.choices(file_choices, k=count)
        for file in selected_files_list:
          # load the image
          new_img = image.open(file)
          
          # optionally blur the image
          if blur_radius > 0.0:
            new_img = new_img.filter(filter.GaussianBlur(radius=blur_radius))
          
          # is this the first image? (regular img2img input counts as the first if given, otherwise this is None)
          if p.init_images[0] is None: # no previous image
            p.init_images[0] = new_img
            continue
          # else, we are compositing with the composite of the previous images
          
          # make size consistent with old image
          old_img = p.init_images[0]
          if new_img.size != old_img.size:
            new_img = new_img.resize(old_img.size)
          
          # make sure we have an alpha channel, and get it
          new_img = new_img.convert('RGBA')
          new_img_alpha = new_img.getchannel('A')
          
          # make opaque parts of new image partially transparent
          fully_transparent = image.new('L', new_img.size, 0)
          paste_channel = image.blend(fully_transparent, new_img_alpha, blend_alpha)
          
          # then composite with the old image
          old_img.paste(new_img, (0, 0), paste_channel) # in place modification


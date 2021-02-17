import os
import argparse
import tensorflow as tf

# trained_checkpoint_prefix = 'checkpoints/dev'
trained_checkpoint_prefix = 'model.ckpt'
checkpoint_dir = os.path.join('MusicTransformer-tensorflow2.0', 'checkpoints')
export_dir = os.path.join(checkpoint_dir, 'converted', '0') # IMPORTANT: each model folder must be named '0', '1', ... Otherwise it will fail!

def convert_model(in_path, out_path):  
  loaded_graph = tf.Graph()
  with tf.compat.v1.Session(graph=loaded_graph) as sess:
      # Restore from checkpoint
      loader = tf.compat.v1.train.import_meta_graph(in_path + '.meta')
      loader.restore(sess, in_path)
      
      # Export checkpoint to SavedModel
      builder = tf.compat.v1.saved_model.builder.SavedModelBuilder(export_dir)
      builder.add_meta_graph_and_variables(sess, ["train", "serve"], strip_default_attrs=True)
      builder.save()


if __name__ == "__main__":
    
    # Parse CLI Args
    parser = argparse.ArgumentParser()

    parser.add_argument('--ckpt_in', default=os.path.join('unconditional_model_16', 'ckpt'), help='path to checkpoint to be converted', type=str)
    parser.add_argument('--ckpt_out', default='ckpt', help='path where checkpoint will be saved', type=str)

    args = parser.parse_args()

    ckpt_in = os.path.join(checkpoint_dir, args.ckpt_in)
    ckpt_out = os.path.join(export_dir, args.ckpt_out)

    convert_model(ckpt_in, ckpt_out)
    
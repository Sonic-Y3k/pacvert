from __future__ import print_function

import argparse


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--codecs', action='store_true')
    parser.add_argument('--version', action='store_true')
    args = parser.parse_args()

    # ---

    if args.version:

        import av._core

        print('PyAV v' + av._core.pyav_version)
        print('git origin: git@github.com:mikeboers/PyAV')
        print('git commit:', av._core.pyav_commit)

        by_config = {}
        for libname, config in sorted(av._core.versions.iteritems()):
            version = config['version']
            if version[0] >= 0:
                by_config.setdefault(
                    (config['configuration'], config['license']),
                    []
                ).append((libname, config))
        for (config, license), libs in sorted(by_config.iteritems()):
            print('library configuration:', config)
            print('library license:', license)
            for libname, config in libs:
                version = config['version']
                print('%-13s %3d.%3d.%3d' % (libname, version[0], version[1], version[2]))

    if args.codecs:
        from av.codec import dump_codecs
        dump_codecs()


if __name__ == '__main__':
    main()

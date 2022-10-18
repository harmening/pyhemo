#FROM python:3.7-slim AS compile-image
#FROM python:3.8-slim AS compile-image
#FROM python:3.9-slim AS compile-image
FROM python:3.10-slim AS compile-image

WORKDIR /

# install c-libraries and other dependencies
RUN apt-get update && apt-get install -qq -y \
			  build-essential libpq-dev --no-install-recommends apt-utils \
        libpython3-dev \
        libsuitesparse-dev \
        gcc \
        g++ \
        gfortran \
        openmpi-bin \
        openmpi-common \
        openssh-client \ 
        openssh-server \
        libeigen3-dev \
        libsuperlu-dev \
        libgts-dev \
        libgts-0.7-5 \
        libc6 \
        libglib2.0-0 \
        libglib2.0-dev \
        libglu1-mesa-dev \
        libfreetype6-dev\
        libxml2-dev \
        libxslt1-dev \
        libmpfr-dev \
        libboost-dev \
        libboost-atomic-dev \
        libboost-chrono-dev \
        libboost-date-time-dev \
        libboost-system-dev \
        libboost-thread-dev \
        libeigen3-dev \
        libgmp-dev \
        libgmpxx4ldbl \
        libtbb-dev \
        libssl-dev \
        wget \ 
        unzip \
        tar \
        csh \
    && python -m venv /opt/venv \
    && apt-get install -y make \
        -y cmake \
        -y python3-dev \
        git \
        sudo \
    && apt-get clean \
    && sudo rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
    
# Install python modules in virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

# clone duneuro
RUN git config --global http.sslverify false \ 
# very very bad but working
    && export GIT_SSL_NO_VERIFY=true \
    && mkdir /duneuro \
    && cd /duneuro \
    && for i in common geometry localfunctions grid istl; do \
	       git clone --branch releases/2.6 https://gitlab.dune-project.org/core/dune-$i.git; \
       done; \
       for i in functions typetree uggrid; do \
	       git clone --branch releases/2.6 https://gitlab.dune-project.org/staging/dune-$i.git; \
       done; \
       for i in pdelab; do \
	       git clone --branch releases/2.6 https://gitlab.dune-project.org/pdelab/dune-$i.git; \
       done; \
       for i in duneuro; do \
	       #git clone --branch releases/2.6 https://gitlab.dune-project.org/duneuro/$i.git; \
	       #git clone https://gitlab.dune-project.org/duneuro/duneuro/-/tree/quick-hack-bst-issue; \
         git clone --branch quick-hack-bst-issue https://gitlab.dune-project.org/duneuro/$i.git; \
       done; \
       for i in duneuro-py; do \
	       git clone --branch releases/2.6 --recursive https://gitlab.dune-project.org/duneuro/$i.git; \
       done \
# small corrections due to missing links
    && cp /duneuro/dune-uggrid/low/*.h /duneuro/dune-uggrid/ug/ \
    && cp /duneuro/dune-uggrid/low/*.h /duneuro/dune-uggrid/ \
    && cp /duneuro/dune-uggrid/low/*.cc /duneuro/dune-uggrid/ug/ \
    && cp /duneuro/dune-uggrid/dom/domain.h /duneuro/dune-uggrid/ug/ \
    && cp /duneuro/dune-uggrid/gm/pargm.h /duneuro/dune-uggrid/ug/ \
    && cp /duneuro/dune-uggrid/gm/cw.* /duneuro/dune-uggrid/ug/ \
    && cp /duneuro/dune-uggrid/np/udm/udm.* /duneuro/dune-uggrid/ug/ \
    && cp /duneuro/dune-uggrid/np/algebra/sm.* /duneuro/dune-uggrid/ug/ \
    && cp /duneuro/dune-uggrid/gm/evm.* /duneuro/dune-uggrid/ug/ \
    && cp /duneuro/dune-uggrid/gm/dlmgr.* /duneuro/dune-uggrid/ug/ \
# 1111 for normal model, 3333 for big model
    && sed -i 's/^.*#define NDELEM_BLKS_MAX\s*1.*$/#define NDELEM_BLKS_MAX                 3333/' /duneuro/dune-uggrid/gm/gm.h \
    && sed -i 's/^.*#define NDELEM_BLKS_MAX\s*1.*$/#define NDELEM_BLKS_MAX                 3333/' /duneuro/dune-uggrid/ug/gm.h \
# compile duneuro
    && MAKE_FLAGS="-j2 --with-superlu=/SuperLU_5.2.1 --with-superlu-lib=/SuperLU_5.2.1/lib/libsuperlu_5.1.a" \
    && for i in common geometry localfunctions grid istl typetree uggrid functions pdelab ; do \
      cd /duneuro/dune-$i; \
      mkdir build; \
      cd build; \
      cmake -G "Unix Makefiles" \
            -DCMAKE_CXX_FLAGS="-fPIC -Og -g -Wall -Wextra -Wno-unused-parameter -Wno-unused-local-typedefs -std=c++14 -pthread -march=native -Wdelete-non-virtual-dtor" \
						-DCMAKE_BUILD_TYPE=Debug \
						-DCMAKE_DISABLE_FIND_PACKAGE_MPI=TRUE\
						-DCMAKE_DISABLE_FIND_PACKAGE_SuperLU=FALSE\
						-DCMAKE_CXX_COMPILER=g++\
						-DCMAKE_C_COMPILER=gcc \
					.. ;\
      make $MAKE_FLAGS; \
      make test; \
      make install; \
    done \
    && for i in duneuro duneuro-py; do \
      cd /duneuro/$i; \
      mkdir build; \
      cd build; \
      cmake -G "Unix Makefiles" \
            -DCMAKE_CXX_FLAGS="-fPIC -Og -g -Wall -Wextra -Wno-unused-parameter -Wno-unused-local-typedefs -std=c++14 -pthread -march=native -Wdelete-non-virtual-dtor" \
						-DCMAKE_BUILD_TYPE=Release \
						-DCMAKE_DISABLE_FIND_PACKAGE_MPI=TRUE\
						-DCMAKE_DISABLE_FIND_PACKAGE_SuperLU=FALSE\
						-DCMAKE_CXX_COMPILER=g++\
						-DCMAKE_C_COMPILER=gcc \
					.. ;\
      make $MAKE_FLAGS; \
      make test; \
      make install; \
    done; 

# install duneuro
RUN echo 'CMAKE_FLAGS="\
          -G \"Unix Makefiles\" \
          -DCMAKE_CXX_FLAGS=\"-fPIC -Og -g -Wall -Wextra -Wno-unused-parameter -Wno-unused-local-typedefs -std=c++14 -pthread -march=native -Wdelete-non-virtual-dtor\" \
					-DCMAKE_BUILD_TYPE=Debug \
					-DCMAKE_DISABLE_FIND_PACKAGE_MPI=TRUE\
					-DCMAKE_DISABLE_FIND_PACKAGE_SuperLU=FALSE\
					-DCMAKE_CXX_COMPILER=g++\
					-DCMAKE_C_COMPILER=gcc \ 
          " MAKE_FLAGS="-j2"' > /duneuro/dune-common/config_release.opts \
    && /duneuro/dune-common/bin/dunecontrol --opts=/duneuro/dune-common/config_release.opts --builddir=/duneuro/build-release all


# install openmeeg
RUN pip3 install \
        numpy \
        openmeeg==2.5.5


#FROM python:3.7-slim AS build-image
#FROM python:3.8-slim AS build-image
#FROM python:3.9-slim AS build-image
FROM python:3.10-slim AS build-image
WORKDIR /

COPY --from=compile-image /opt/venv /opt/venv
COPY --from=compile-image /usr/lib/x86_64-linux-gnu/* /usr/lib/x86_64-linux-gnu/ 
COPY --from=compile-image /duneuro/build-release/duneuro-py/src /duneuro_src

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH "${PYTHONPATH}:/duneuro_src/"
ENV LD_LIBRARY_PATH "${LD_LIBRARY_PATH}:/usr/local/lib/"

ADD . /pyhemo

# Install pyhemo and run tests
RUN apt-get update && apt-get install -qq -y vim \
    && cd /pyhemo \
    && pip3 install -r requirements.txt \
    && python setup.py develop \
    && pytest tests
 

CMD ["python"]

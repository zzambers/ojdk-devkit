%global centos5_arches x86_64 %ix86
%global centos7_altarches aarch64 ppc64 ppc64le %arm
# we do not want debug packages
%global debug_package %{nil}

Name: ojdk-devkit-8
Version: 0.1
Release: 10%{?dist}
Summary: OpenJDK devkit 8

# License TODO: should include license of all rpms unpacked to sysroot?
License: GPLv2
URL: http://openjdk.java.net/
Source0: https://github.com/openjdk/jdk8u/archive/refs/tags/jdk8u382-ga.tar.gz
Source1: gcc-7.3.0-ppc64.patch

BuildRequires: make autoconf automake libtool gcc gcc-c++ wget glibc-devel texinfo tar
%ifarch x86_64
BuildRequires: glibc-devel(x86-32) libgcc(x86-32) libstdc++-devel(x86-32)
%endif
# for testing
BuildRequires: java-1.8.0-openjdk-devel
# curently no requires
#Requires:

%description
OpenJDK devkit 8

%prep
%setup -q -n jdk8u-jdk8u382-ga

# fix mpc download link
sed -i 's;http://www.multiprecision.org/mpc/download/;https://ftp.gnu.org/gnu/mpc/;g' make/devkit/Tools.gmk
%if 0%{?rhel} > 7
# versions of some tools are too old -> not buildable on rhel-8 (in particular gcc)
# Update to newer versions from:
# https://github.com/openjdk/jdk11u-dev/blob/d0f6931ab7f9e3ad30365abfa862958820035ee3/make/devkit/Tools.gmk#L92
sed -i 's;binutils-2.24;binutils-2.30;g' make/devkit/Tools.gmk
sed -i 's;gcc-4.8.2;gcc-7.3.0;g' make/devkit/Tools.gmk
sed -i 's;ccache-3.1.9;ccache-3.3.6;g' make/devkit/Tools.gmk
sed -i 's;mpfr-3.0.1;mpfr-3.1.5;g' make/devkit/Tools.gmk
sed -i 's;gmp-4.3.2;gmp-6.1.2;g' make/devkit/Tools.gmk
sed -i 's;mpc-1.0.1;mpc-1.0.3;g' make/devkit/Tools.gmk
# newer versions not available as .tar.bz2
sed -i 's;$(gcc_ver).tar.bz2;$(gcc_ver).tar.gz;g' make/devkit/Tools.gmk
# Fix build on ppc64le, see: https://gcc.gnu.org/bugzilla/show_bug.cgi?id=86162
cp %{SOURCE1} make/devkit/gcc-7.3.0.patch
%endif
# fontconfig is in RPM_LIST (configure fails without it)
sed -i 's;RPM_LIST :=;& fontconfig fontconfig-devel zlib zlib-devel libpng libpng-devel bzip2-libs bzip2-devel;g' make/devkit/Tools.gmk
# better debugging (print corresponding log after failure)
sed -i -E 's#> ([$][(][@<]D[)]/log[.][a-z]*) 2>&1#& || { cat \1 ; false ; }#g' make/devkit/Tools.gmk
%ifnarch x86_64 %ix86
sed -i "s;RPM_ARCHS :=.*;RPM_ARCHS := $(uname -m);g" make/devkit/Tools.gmk
%ifarch s390x
# s390x build of gcc on f19 also needs s390 rpms (gnu/stubs-32.h from glibc-devel)
sed -i 's;RPM_ARCHS :=;& s390;g' make/devkit/Tools.gmk
%endif
%endif
# also match noarch rpms
sed -i 's;RPM_ARCHS :=;& noarch;g' make/devkit/Tools.gmk

# use CentOS packages with fallback to Fedora
pushd make/devkit
# Rpms are not downloaded automatically as part of devkit generation on JDK8 (unlike on newer JDKs)
# extract RPM_LIST from Tools.gmk
cat Tools.gmk | sed -n  '/^RPM_LIST/,/^$/p' > dlrpms.mk
echo 'ARCH := $(shell uname -m)' >> dlrpms.mk
echo 'BASE_URL := https://archives.fedoraproject.org/pub/archive/fedora-secondary/releases/19/Everything/$(ARCH)/os/Packages/' >> dlrpms.mk
%ifarch %{centos5_arches}
# Use Centos6 as Centos5 has too old freetype (does not support LCD Filter)
# needed since: https://github.com/openjdk/jdk8u/commit/3409a5b3b2d5d6b1ef0d3f0f861935b2b9d36993
# CentOS6 packages are only available on x86_64, i386
sed -i 's;^BASE_URL :=.*;BASE_URL := https://vault.centos.org/6.10/os/$(ARCH)/Packages/;g' dlrpms.mk
%endif
%ifarch %{centos7_altarches}
# CentOS7 (altarch) packages are available on aarch64, ppc64, ppc64le arm
sed -i 's;^BASE_URL :=.*;BASE_URL := https://vault.centos.org/altarch/7.8.2003/os/$(ARCH)/Packages/;g' dlrpms.mk
%endif
echo 'download-rpms:' >> dlrpms.mk
echo '	mkdir rpms' >> dlrpms.mk
# trick from devkit of later jdks
echo '	wget -r -e robots=off -P rpms -np -nd $(patsubst %%, -A "*%%*.rpm", $(RPM_LIST)) $(BASE_URL)' >> dlrpms.mk
cat dlrpms.mk
make -f dlrpms.mk download-rpms
%ifarch x86_64
# x86_64 devkit also wants i386 packages, x86_64 repo also contains these,
# but *-headers packages are missing required for gcc build,
# x86_64 ones are universal (multilib) -> just make a copy as i386
for file in rpms/*headers*.x86_64.rpm ; do
	file386="${file%.x86_64.rpm}.i386.rpm"
	file686="${file%.x86_64.rpm}.i686.rpm"
	if ! [ -e "${file386}" ] && ! [ -e "${file686}" ] ; then
		cp "${file}" "${file386}"
	fi
done
%endif
ls rpms
popd

%build
pushd make/devkit
make RPM_DIR="$(pwd)/rpms" \
%ifnarch x86_64
cpu=$(uname -m) platforms=$(uname -m)-unknown-linux-gnu \
%endif
all tars
popd

%install
mkdir -p %{buildroot}%{_datadir}/%{name}
cp -p build/devkit/result/*.tar.gz %{buildroot}%{_datadir}/%{name}/

%check
# check if jdk can be build using devkit
mkdir devkit
%ifarch x86_64
# on x86_64 there are archives for both i386 and x86_64, unpack one for x86_64
tar -C devkit -xf %{buildroot}%{_datadir}/%{name}/*x86_64*.tar.gz
%else
tar -C devkit -xf %{buildroot}%{_datadir}/%{name}/*.tar.gz
%endif
rm -rf build
DEVKIT_ROOT="$(pwd)/devkit" host="$(uname -m)-unknown-linux-gnu" . devkit/devkit.info

bash configure \
%ifnarch x86_64 %ix86
--with-freetype-lib="${DEVKIT_SYSROOT}/usr/lib64" \
--with-freetype-include="${DEVKIT_SYSROOT}/usr/include/freetype2" \
%endif
--with-devkit="$(pwd)/devkit" --with-boot-jdk=/usr/lib/jvm/java-1.8.0-openjdk
[ -f config.log ] && cat config.log
make images
build/*/images/j2sdk-image/bin/java -version

%files
%{_datadir}/%{name}

%changelog
